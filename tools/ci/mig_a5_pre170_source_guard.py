#!/usr/bin/env python3
"""MIG-A5 source-only guard for the experimental PRE170 Android SDL pump patch.

This is not an Android build or evidence of runtime compatibility.
The private PRE99/V51 source was previously authenticated in a separate
Drive-backed Actions-only gate. This guard uses only the public fork.
"""
from __future__ import annotations
import hashlib
import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
H = ROOT / "nativo/sdk/include/rex/input/sdl/sdl_input_driver.h"
CPP = ROOT / "nativo/sdk/src/input/sdl/sdl_input_driver.cpp"
SYSTEM = ROOT / "nativo/sdk/src/input/input_system.cpp"
PIN_V51_HEADER = "6b532f228805dbd57aaaa3d4e19d6febf784506ebacd6b80216af254cae2f5ca"

def check_source() -> None:
    header = H.read_bytes()
    cpp = CPP.read_text(encoding="utf-8-sig")
    system = SYSTEM.read_text(encoding="utf-8-sig")
    assert hashlib.sha256(header).hexdigest() == PIN_V51_HEADER, "V51 SDL header drifted"
    for token in (
        "#include <chrono>  // NFSMW_PRE170",
        "#if REX_PLATFORM_ANDROID",
        "std::chrono::steady_clock::now().time_since_epoch()",
        "constexpr int64_t kMinIntervalNs = 8'000'000;",
        "sdl_next_pump_ns_.compare_exchange_weak(",
        "std::memory_order_relaxed, std::memory_order_relaxed",
        "SDL_PumpEvents();",
        "sdl_pumpevents_queued_.compare_exchange_strong(",
    ):
        assert token in cpp, "PRE170 expected token absent: " + token
    assert cpp.count("NFSMW_PRE170") == 2, "Duplicate PRE170 comments"
    assert cpp.count("void SDLInputDriver::QueueControllerUpdate()") == 1
    # Exact PRE170 block from the authenticated private V51 SDK input review.
    method_prefix = cpp.split("void SDLInputDriver::QueueControllerUpdate() {\n", 1)[1].split("  // Pump SDL events", 1)[0]
    expected_pre170_hash = "0831a7b2e99a702b3dc2d0a7b6f8f961059ca2b261ab0999ad1e4a92322d07d4"
    assert hashlib.sha256(method_prefix.encode("utf-8")).hexdigest() == expected_pre170_hash, "PRE170 V51 block mismatch"
    print("MIG_A5_PRE170_V51_BLOCK_SHA_MATCH=TRUE")
    method = cpp[cpp.index("void SDLInputDriver::QueueControllerUpdate()"):]
    method = method[:method.index("inline uint64_t SDLInputDriver::AnalogToKeyfield")]
    assert method.count("#if REX_PLATFORM_ANDROID") == 1
    assert method.count("#endif") == 1
    assert method.index("#endif") < method.index("SDL_PumpEvents();")
    # No PRE364 log instrumentation from the old V51 diagnostic.
    assert "NFSMW_PRE364_XINPUT_USER0" not in system
    # Existing touch bridge should remain in the SDK source unchanged.
    assert "rex_sdl_set_touch_gamepad_state" in cpp
    print("MIG_A5_V51_PRE170_HEADER_SHA_MATCH=TRUE")
    print("MIG_A5_PRE170_SOURCE_STRUCTURE_PASS=TRUE")
    print("MIG_A5_PRE364_DIAGNOSTIC_NOT_PORTED=TRUE")


SYNTHETIC = r"""
#include <atomic>
#include <cstdint>
#include <thread>
#include <vector>
#include <iostream>
struct Gate {
 std::atomic<std::int64_t> sdl_next_pump_ns_{0};
 bool allow(std::int64_t now_ns) {
    constexpr int64_t kMinIntervalNs = 8'000'000;
    int64_t next_ns = sdl_next_pump_ns_.load(std::memory_order_relaxed);
    while (true) {
      if (now_ns < next_ns) return false;
      if (sdl_next_pump_ns_.compare_exchange_weak(
          next_ns, now_ns + kMinIntervalNs,
          std::memory_order_relaxed, std::memory_order_relaxed)) break;
    }
    return true;
 }
};
int main() {
 Gate g;
 if (!g.allow(1) || g.allow(7'999'999) || g.allow(8'000'000)
     || !g.allow(8'000'001)) return 10;
 Gate concurrent;
 std::atomic<int> allowed{0};
 std::vector<std::thread> workers;
 for(int i=0;i<24;i++)
   workers.emplace_back([&] { if (concurrent.allow(123456789)) ++allowed; });
 for(auto& t: workers) t.join();
 if(allowed.load()!=1) return 11;
 if(!concurrent.allow(131456789)) return 12;
 std::cout << "MIG_A5_ATOMIC_GATE_SYNTHETIC_PASS=TRUE\n";
}
"""

def check_synthetic_host_compile() -> None:
    with tempfile.TemporaryDirectory(prefix="nfsmw_mig_a5_test_") as td:
        src = pathlib.Path(td) / "test.cpp"
        exe = pathlib.Path(td) / "test"
        src.write_text(SYNTHETIC, encoding="utf-8")
        subprocess.run(["g++", "-std=c++20", "-O2", "-Wall", "-Wextra",
                        "-Werror", "-pthread", str(src), "-o", str(exe)],
                       check=True, timeout=50)
        subprocess.run([str(exe)], check=True, timeout=30)

if __name__ == "__main__":
    check_source()
    check_synthetic_host_compile()
    print("MIG_A5_SOURCE_ONLY_PASS=TRUE")
    print("MIG_A5_ARM64_BUILD_DONE=FALSE")
    print("MIG_A5_RUNTIME_GAMEPAD_VERIFIED=FALSE")
