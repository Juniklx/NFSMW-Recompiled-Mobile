#!/usr/bin/env python3
"""Offline, read-only sanity checks for the public NFSMW fork.

This CI stage intentionally does not try to generate proprietary game code,
compile a playable APK, access signing material, or publish anything.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

EXPECTED_PACKAGE = "io.github.nfsmwrecomp"
PRIVATE_SUFFIXES = (".iso", ".xex", ".xexp", ".p12", ".pfx", ".jks", ".keystore", ".nfsp")
REQUIRED = (
    "android/app/build.gradle.kts",
    "android/gradlew",
    "nativo/app/CMakeLists.txt",
    "nativo/app/nfsmw_movil.toml",
    "nativo/.gitignore",
    "nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp",
    "tools/android/preparar_nativo.py",
)


def inspect(root: Path, tracked: list[str]) -> dict:
    errors = []
    for path in REQUIRED:
        if not (root / path).is_file():
            errors.append(f"missing_required_file:{path}")
    forbidden = [path for path in tracked if path.lower().endswith(PRIVATE_SUFFIXES)]
    if forbidden:
        errors.append("game_or_signing_material_is_tracked: " + ", ".join(forbidden[:15]))
    if any(path.startswith("nativo/app_usa/generated/") or
           path.startswith("nativo/app/generated/") or
           path.startswith("app/generated-android/") for path in tracked):
        errors.append("generated_game_sources_are_tracked")

    gradle = root / "android/app/build.gradle.kts"
    source = gradle.read_text(encoding="utf-8") if gradle.is_file() else ""
    def match(pattern):
        m = re.search(pattern, source, re.MULTILINE)
        return m.group(1) if m else None
    package = match(r'^\s*applicationId\s*=\s*"([^"]+)"')
    version_text = match(r'^\s*versionCode\s*=\s*(\d+)')
    version = int(version_text) if version_text else None
    abi_ok = bool(re.search(r'abiFilters\s*\+=\s*"arm64-v8a"', source))
    debug_release_signing = 'signingConfig = signingConfigs.getByName("debug")' in source
    if package != EXPECTED_PACKAGE:
        errors.append("android_application_id_mismatch")
    if version is None:
        errors.append("version_code_missing_or_not_literal")
    if not abi_ok:
        errors.append("arm64_abi_filter_not_confirmed")
    return {
        "check": "SOURCE_ONLY",
        "ok": not errors,
        "errors": errors,
        "tracked_files": len(tracked),
        "android_package": package,
        "upstream_version_code": version,
        "target_baseline_version_code": 51,
        "release_must_increment_beyond_baseline": version is None or version <= 51,
        "debug_signing_in_release": debug_release_signing,
        "playable_apk_built": False,
        "release_signed": False,
        "game_assets_or_generated_cpp_supplied": False,
        "device_tested": False,
        "fps_gain_proven": False,
        "next_gate": "Authenticate V51 source/patches; verify private data provenance and disk budget before any signed release",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    root = a.root.resolve()
    r = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, check=True)
    tracked = [f for f in r.stdout.decode("utf-8", errors="replace").split("\0") if f]
    report = inspect(root, tracked)
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    print(serialized)
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(serialized, encoding="utf-8")
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
