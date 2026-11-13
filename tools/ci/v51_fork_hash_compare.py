#!/usr/bin/env python3
"""MIG-A2: compare public-fork source hashes with seven PRE696 V51 pins.

This is a SOURCE-ONLY, non-causal comparison. It never downloads or writes game
code, signs an APK, patches a source, or opens signing material.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

MANIFEST_PATH = Path(__file__).with_name("v51_pre696_pinned_manifest.json")
EXPECTED_PATHS = (
    "nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp",
    "nativo/sdk/include/rex/ui/vulkan/presenter.h",
    "nativo/app/src/nfsmw_ajustes_graficos.cpp",
    "nativo/app/src/nfsmw_nativo_sistema.cpp",
    "nativo/app/src/nfsmw_nativo_destinos.cpp",
    "android/app/src/main/java/io/github/nfsmwrecomp/MotorNativo.java",
    "android/app/src/main/java/io/github/nfsmwrecomp/Ajustes.java",
)
PINNED_ZIP_SHA = "d06e06d4dda54d4b50924ec5a404ef396c91cef2166f7b9e055f4b5910154075"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compare(root: Path, manifest: dict) -> dict:
    if manifest.get("schema") != 1:
        raise ValueError("MIG_A2_MANIFEST_SCHEMA_MISMATCH")
    reference = manifest.get("source_artifact", {})
    if reference.get("sha256") != PINNED_ZIP_SHA:
        raise ValueError("MIG_A2_REFERENCE_ARTIFACT_SHA_MISMATCH")
    if reference.get("replayed_V51_binaries_equivalent_to_signed_APK") is not False:
        raise ValueError("MIG_A2_BINARY_PROVENANCE_CLAIM_UNSAFE")
    files = manifest.get("files")
    if not isinstance(files, list) or [f.get("path") for f in files] != list(EXPECTED_PATHS):
        raise ValueError("MIG_A2_UNEXPECTED_PATH_SET")
    result = []
    for ref in files:
        name = ref["path"]
        pin = ref.get("sha256")
        size = ref.get("bytes")
        if not isinstance(pin, str) or not re.fullmatch(r"[0-9a-f]{64}", pin):
            raise ValueError("MIG_A2_INVALID_HASH")
        if type(size) is not int or size <= 0:
            raise ValueError("MIG_A2_INVALID_SIZE")
        p = root / name
        if not p.is_file() or p.is_symlink():
            status = "MISSING_OR_UNSAFE"
            found_sha = None
            found_bytes = None
        else:
            b = p.read_bytes()
            found_sha, found_bytes = sha256(b), len(b)
            status = "IDENTICAL" if (found_sha, found_bytes) == (pin, size) else "DIFFERENT"
        result.append({
            "path": name,
            "status": status,
            "v51_authenticated_sha256": pin,
            "fork_sha256": found_sha,
            "v51_bytes": size,
            "fork_bytes": found_bytes,
        })
    counts = {x: sum(r["status"] == x for r in result)
              for x in ("IDENTICAL", "DIFFERENT", "MISSING_OR_UNSAFE")}
    return {
        "stage": "MIG_A2_V51_TO_FORK_V057_FINGERPRINTS",
        "status": "PASS_PINNED_HASH_COMPARISON" if counts["MISSING_OR_UNSAFE"] == 0 else "FAIL_MISSING_SOURCE",
        "reference": "PRE696_V51_AUTHENTICATED_RECIPE_ONLY",
        "reference_zip_sha256": PINNED_ZIP_SHA,
        "scope": "seven-file hash/size comparison; not a semantic diff",
        "counts": counts,
        "files": result,
        "v51_apk_source_binary_equivalence_proven": False,
        "v51_patches_ported": False,
        "apk_built": False,
        "release_signed": False,
        "device_tested": False,
        "fps_gain_proven": False,
        "next_gate": "Restore/reconcile private V51 recipe and compare changed code hunks, then port safe patches in separate PR",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    a = parser.parse_args()
    if a.self_test:
        assert sha256(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        m = json.loads(MANIFEST_PATH.read_text())
        assert len(m["files"]) == 7
        assert m["source_artifact"]["sha256"] == PINNED_ZIP_SHA
        print("MIG_A2_LOCAL_SELF_TEST=PASS")
        return
    m = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    report = compare(a.root.resolve(), m)
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    print(output)
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(output, encoding="utf-8")
    if report["status"] != "PASS_PINNED_HASH_COMPARISON":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
