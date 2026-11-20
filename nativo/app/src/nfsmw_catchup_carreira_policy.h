// PRE744 career-only Catch-Up policy. Pure function, no game memory or side effects.
// Constants validated in the original USA guest generated code (PRE741–PRE743B).
#pragma once

#include <cstdint>

namespace nfsmw::catchup_carreira {

inline constexpr uint32_t kRaceStatusGlobal = 0x82A2CB18u;
inline constexpr uint32_t kOffsetContexto = 6700u;
inline constexpr uint32_t kContextoCarreira = 2u;

constexpr bool Neutralizar(bool ativado, uint32_t race_status, uint32_t singleton,
                           uint32_t contexto, uint32_t output, uint32_t skill) noexcept {
  return ativado && race_status != 0 && race_status == singleton &&
         contexto == kContextoCarreira && output != 0 && skill != 0;
}

}  // namespace nfsmw::catchup_carreira
