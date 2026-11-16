#!/usr/bin/env python3
"""Compile the real SDL input translation unit with the Android SDK build graph.

No game data, signing material, Gradle packaging, or device execution is used.
Only a JSON evidence report is suitable for upload; objects stay on the runner.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
NDK_VERSION = "28.2.13676358"
PINS = {
    "nativo/sdk/include/rex/input/sdl/sdl_input_driver.h": "6b532f228805dbd57aaaa3d4e19d6febf784506ebacd6b80216af254cae2f5ca",
    "nativo/sdk/src/input/sdl/sdl_input_driver.cpp": "cdb414860777cf222612b98e46280c2e3349adbbfbb5d0eb8f94e4dd0dc76ea1",
}

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, **kwargs)

def main():
    output = Path(os.environ["RUNNER_TEMP"]) / "mig-a6-arm64-input.json"
    build = Path(os.environ["RUNNER_TEMP"]) / "mig-a6-sdk-build"
    report = {"gate": "MIG_A6", "status": "FAIL", "stage": "source_pins",
              "apk_built": False, "full_sdk_linked": False,
              "device_tested": False, "fps_gain_measured": False}
    try:
        report["checkout_commit"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        report["sources"] = {p: sha(ROOT / p) for p in PINS}
        if report["sources"] != PINS:
            raise RuntimeError("PRE170 source fingerprint mismatch")
        sdk = Path(os.environ["ANDROID_HOME"])
        ndk = sdk / "ndk" / NDK_VERSION
        if not (ndk / "build/cmake/android.toolchain.cmake").is_file():
            raise RuntimeError("Pinned Android NDK missing")
        report["ndk"] = NDK_VERSION
        report["api"] = 26
        report["abi"] = "arm64-v8a"
        report["stage"] = "dependencies"
        # The repository helper pins rexglue-sdk to c94f5eb... and preserves
        # the vendored changes instead of replacing the SDK sources.
        helper = ROOT / "nativo/tools/fetch_thirdparty.py"
        report["dependency_helper_sha256"] = sha(helper)
        run([sys.executable, helper], cwd=ROOT / "nativo", timeout=1200)
        if {p: sha(ROOT / p) for p in PINS} != PINS:
            raise RuntimeError("Source changed while restoring dependencies")
        report["stage"] = "configure"
        cmake = sdk / "cmake/3.31.6/bin/cmake"
        ninja = sdk / "cmake/3.31.6/bin/ninja"
        run([cmake, "-S", ROOT / "nativo/sdk", "-B", build, "-G", "Ninja",
             f"-DCMAKE_MAKE_PROGRAM={ninja}",
             f"-DCMAKE_TOOLCHAIN_FILE={ndk}/build/cmake/android.toolchain.cmake",
             "-DANDROID_ABI=arm64-v8a", "-DANDROID_PLATFORM=android-26",
             "-DANDROID_STL=c++_shared", "-DCMAKE_BUILD_TYPE=Release",
             "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON", "-DREXGLUE_BUILD_TESTS=OFF"], timeout=300)
        report["stage"] = "compile"
        # Exact Ninja object target: use the real CMake includes, definitions
        # and precompiled header, without linking a complete game or SDK.
        target = "src/input/CMakeFiles/rexinput.dir/sdl/sdl_input_driver.cpp.o"
        commands = json.loads((build / "compile_commands.json").read_text())
        matches = [c for c in commands if Path(c["file"]).resolve() ==
                   (ROOT / "nativo/sdk/src/input/sdl/sdl_input_driver.cpp").resolve()]
        if len(matches) != 1:
            raise RuntimeError("Expected one real SDL driver compile command")
        command = matches[0]["command"]
        if "aarch64" not in command or "android26" not in command:
            raise RuntimeError("Compile command is not Android ARM64 API 26")
        report["compile_command"] = command.replace(str(ROOT), "<checkout>").replace(str(build), "<build>").replace(str(sdk), "<android-sdk>")
        run([ninja, "-C", build, "-j2", target], timeout=900)
        report["stage"] = "verify_object"
        obj = build / target
        data = obj.read_bytes()
        if data[:6] != b"\x7fELF\x02\x01" or struct.unpack_from("<HH", data, 16) != (1, 183):
            raise RuntimeError("Object is not ELF64 little-endian AArch64 relocatable")
        nm = ndk / "toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-nm"
        symbols = subprocess.check_output([str(nm), "-C", str(obj)], text=True)
        required = ["SDLInputDriver::QueueControllerUpdate()", "rex_sdl_set_touch_gamepad_state"]
        if not all(s in symbols for s in required):
            raise RuntimeError("Expected SDL input and touch bridge symbols absent")
        report["object"] = {"target": target, "bytes": len(data), "sha256": sha(obj),
                            "elf_type": "ET_REL", "machine": "AArch64", "required_symbols": required}
        report["status"] = "PASS_REAL_ANDROID_ARM64_INPUT_OBJECT"
        report["stage"] = "complete"
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        output.write_text(json.dumps(report, indent=2) + "\n")
        print("MIG_A6_STATUS=" + report["status"], flush=True)
        print("MIG_A6_STAGE=" + report["stage"], flush=True)

if __name__ == "__main__":
    main()
