// PRE744 pure policy tests: no Xbox assets or Android signing needed.
#include "../nfsmw_catchup_carreira_policy.h"
#include <cassert>

using nfsmw::catchup_carreira::Neutralizar;

constexpr unsigned kObj = 0x80001000u;
constexpr unsigned kOutput = 0x80002000u;
constexpr unsigned kSkill = 0x80003000u;

static_assert(Neutralizar(true, kObj, kObj, 2, kOutput, kSkill));
static_assert(!Neutralizar(false, kObj, kObj, 2, kOutput, kSkill));
static_assert(!Neutralizar(true, kObj, kObj, 0, kOutput, kSkill));  // Quick Race
static_assert(!Neutralizar(true, kObj, kObj, 1, kOutput, kSkill));  // Online
static_assert(!Neutralizar(true, kObj, kObj, 3, kOutput, kSkill));  // Other
static_assert(!Neutralizar(true, kObj, kObj + 4, 2, kOutput, kSkill));  // Wrong singleton
static_assert(!Neutralizar(true, 0, 0, 2, kOutput, kSkill));
static_assert(!Neutralizar(true, kObj, kObj, 2, 0, kSkill));
static_assert(!Neutralizar(true, kObj, kObj, 2, kOutput, 0));

int main() {
  assert(Neutralizar(true, kObj, kObj, 2, kOutput, kSkill));
  assert(!Neutralizar(true, kObj, kObj, 0, kOutput, kSkill));
  return 0;
}
