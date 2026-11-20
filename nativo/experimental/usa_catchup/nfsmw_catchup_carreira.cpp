// PRE747 USA-only catchup experiment: this source MUST be staged into
// nativo/app_usa/src inside the authenticated private build workspace.
// DO NOT link into nativo/app (PAL). Never merge into a release without
// real USA native link and negative-control gameplay tests.
// PRE744 -- candidate: neutralize dynamic AI Catch-Up ONLY in Career (Xbox 360 USA).
//
// Authenticated PRE745/PRE746 original USA guest code:
//  sub_821060A8 -> sub_823328C0 (GRaceStatus::ComputeCatchUpSkill).
//  r3=this GRaceStatus, r4=racer info, r5=PID, r6=output*, r7=skill*,
//  r8=off_world. sub_823328C0 reads this+6700 (context 0=Quick Race,
//  2=Career), this+6704 (race params), writes two float outputs, and returns
//  a bool in r3. The Career branch does NOT consult the CatchUp attribute.
//
// A safe-observation feature candidate, not a release-tested fix:
//  - cvar is OFF by default until runtime and negative-control testing.
//  - invoke the game's original code in every mode, including Career;
//  - if the same authenticated GRaceStatus singleton is still in context 2,
//    replace only the two dynamic catchup outputs with float 0.0 and bool false;
//  - do not alter base AI skill, acceleration/handling physics, game data or saves.
// This code must not be shipped as enabled without validating real races,
// Quick Race unaffected, and the game's distinct GetCatchupCheat path.

#include <atomic>
#include <cstdint>
#include <cstring>

#include <rex/cvar.h>
#include <rex/hook.h>
#include <rex/logging.h>

#include "nfsmw_catchup_carreira_policy.h"

REXCVAR_DEFINE_BOOL(nfsmw_sem_catchup_carreira, false, "NFSMW",
                    "Experimental: neutralizar o Catch-Up dinamico da IA somente nas provas de Carreira")
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);

namespace {
std::atomic<uint64_t> g_catchup_neutralizacoes{0};

uint32_t LerGuestBE32(const uint8_t* base, uint32_t endereco) {
  uint32_t v = 0;
  std::memcpy(&v, base + endereco, sizeof(v));
  return __builtin_bswap32(v);
}

void GravarFloatZero(uint8_t* base, uint32_t endereco) {
  // IEEE-754 0.0f = 00000000, identical byte order in both endian layouts.
  std::memset(base + endereco, 0, sizeof(uint32_t));
}
}  // namespace

REX_EXTERN(__imp__sub_823328C0);
REX_HOOK_RAW(sub_823328C0) {
  const uint32_t race_status = ctx.r3.u32;
  const uint32_t output = ctx.r6.u32;
  const uint32_t skill = ctx.r7.u32;
  const bool configurado = REXCVAR_GET(nfsmw_sem_catchup_carreira);

  uint32_t singleton = 0;
  uint32_t contexto = 0;
  if (configurado && race_status != 0 && output != 0 && skill != 0) {
    singleton = LerGuestBE32(base, nfsmw::catchup_carreira::kRaceStatusGlobal);
    if (singleton == race_status) {
      contexto = LerGuestBE32(base, race_status + nfsmw::catchup_carreira::kOffsetContexto);
    }
  }
  const bool neutralizar = nfsmw::catchup_carreira::Neutralizar(
      configurado, race_status, singleton, contexto, output, skill);

  // Preserve original side effects and all behavior in Quick Race / other modes.
  __imp__sub_823328C0(ctx, base);

  if (!neutralizar) {
    return;
  }

  GravarFloatZero(base, output);
  GravarFloatZero(base, skill);
  ctx.r3.u64 = 0;  // bool false: caller does not apply dynamic glue/catchup.

  const uint64_t n = g_catchup_neutralizacoes.fetch_add(1, std::memory_order_relaxed) + 1;
  if (n == 1 || n == 256 || n == 4096) {
    REXLOG_INFO("[PRE744] Career-only Catch-Up neutralizado: chamadas={}, contexto=2", n);
  }
}
