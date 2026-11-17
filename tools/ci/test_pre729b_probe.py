#!/usr/bin/env python3
"""Regression tests for observed Android layer wrappers and empty Perfetto output.

All Android commands are mocked. No physical device capability is inferred.
"""
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/diagnostics/nfsmw_pre729b_probe_capture.sh"
NAME = "test SurfaceView[io.github.nfsmwrecomp/io.github.nfsmwrecomp.GameActivity]@0"
BLAST = NAME + "(BLAST)#103"
WRAPPED = "\n".join([
    f"RequestedLayerState{{Background for {NAME}#104 parentId=102 z=-2147483648}}",
    f"RequestedLayerState{{{NAME}#102 parentId=101 z=-2}}",
    f"RequestedLayerState{{{BLAST} parentId=102}}",
])
MOCK = '''#!/bin/sh
name=${0##*/}
printf '%s %s\\n' "$name" "$*" >> "$TEST_CALLS"
case "$name" in
 id) echo "$TEST_UID";;
 sleep) :;;
 getprop) echo running;;
 perfetto)
   [ "$TEST_PERFETTO_RC" = 0 ] || exit "$TEST_PERFETTO_RC"
   [ "$TEST_PERFETTO_EMPTY" = 0 ] || exit 0
   echo 'linux.ftrace available';;
 atrace) echo 'gfx - Graphics';;
 dumpsys)
  case "$1" in
   package) echo "versionCode=$TEST_VERSION minSdk=26";;
   thermalservice) echo 'Thermal Status: 0'; echo 'IsStatusOverride: false';;
   SurfaceFlinger)
    if [ "$2" = --list ]; then
     cat "$TEST_LAYER_FILE"
     exit "$TEST_LIST_RC"
    elif [ "$2" = --latency ]; then
     [ "$#" = 3 ] && [ "$3" = "$TEST_SELECTED" ] || exit 98
     echo 8333333
     if [ "$TEST_HEADER_ONLY" = 0 ]; then
      echo '1000000000 1000000001 1000000002'
      echo '0 0 0'
      echo '2000000000 9223372036854775807 2000000002'
     fi
     exit "$TEST_LATENCY_RC"
    else exit 99; fi;;
   *) exit 97;;
  esac;;
esac
'''

def case(layers=WRAPPED, selected=BLAST, uid="2000", version="51", empty="0",
         perfetto_rc="0", expected=0, header_only="0", list_rc="0", latency_rc="0"):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        bindir = root / "bin"
        bindir.mkdir()
        for name in ("id", "sleep", "getprop", "perfetto", "atrace", "dumpsys"):
            p = bindir / name
            p.write_text(MOCK)
            p.chmod(0o755)
        (root / "layers").write_text(layers + "\n")
        env = dict(os.environ, PATH=str(bindir) + os.pathsep + os.environ["PATH"],
                   TEST_CALLS=str(root / "calls"), TEST_UID=uid, TEST_VERSION=version,
                   TEST_LAYER_FILE=str(root / "layers"), TEST_SELECTED=selected,
                   TEST_PERFETTO_RC=perfetto_rc, TEST_PERFETTO_EMPTY=empty,
                   TEST_HEADER_ONLY=header_only, TEST_LIST_RC=list_rc,
                   TEST_LATENCY_RC=latency_rc)
        result = subprocess.run(["sh", str(SCRIPT), "0", str(root)], env=env,
                                capture_output=True, text=True, timeout=15)
        assert result.returncode == expected, result.stdout + result.stderr
        files = list(root.glob("NFSMW_PRE729B_CAPACIDADE_*.txt"))
        if expected:
            assert not files
        else:
            assert len(files) == 1
            text = files[0].read_text()
            assert "PRE729B_CAPABILITY_RECORDED_REQUIRES_ANALYSIS" in text
            if selected:
                assert "SELECTED_SURFACE=" + selected + "\n" in text, text
                valid = 0 if header_only == "1" else 1
                assert text.count("VALID_TRIPLE_ROWS=" + str(valid)) == 3, text
                if valid and latency_rc == "0":
                    assert text.count("LATENCY_DATA=NUMERIC_TRIPLES_PRESENT_NOT_YET_VALIDATED") == 3
                else:
                    assert text.count("LATENCY_DATA=UNCONFIRMED") == 3
            else:
                assert "LATENCY_SKIPPED=NO_UNIQUE_GAME_SURFACE" in text
                assert "BEGIN=LATENCY_" not in text
            if empty == "1":
                assert "PERFETTO_SERVICE_DATA=EMPTY_UNCONFIRMED" in text
                assert "OUTPUT_STATE=EMPTY_UNCONFIRMED" in text
                assert "PERFETTO_SERVICE_DATA=TEXT_PRESENT" not in text
            if perfetto_rc != "0":
                assert "COMMAND_RC=" + perfetto_rc in text
        calls = (root / "calls").read_text()
        assert "--latency-clear" not in calls and "--timestats" not in calls
        assert "override-status" not in calls
        for line in calls.splitlines():
            if line.startswith("perfetto "):
                assert line in ("perfetto --version", "perfetto --query", "perfetto --help")

if __name__ == "__main__":
    subprocess.run(["sh", "-n", str(SCRIPT)], check=True)
    case()
    case(uid="10000", expected=10)
    case(version="52", expected=12)
    case(layers="", selected="")
    case(layers=WRAPPED + "\n" + NAME + "(BLAST)#105", selected="")
    case(perfetto_rc="124")
    case(empty="1")
    case(layers=NAME + "#101", selected=NAME + "#101")
    case(layers=NAME + "#101\n" + NAME + "#102", selected="")
    case(layers=WRAPPED + "\nRequestedLayerState{" + BLAST + " parentId=102}")
    case(header_only="1")
    case(list_rc="1", selected="")
    case(latency_rc="1")
    case(layers=WRAPPED.replace("io.github.nfsmwrecomp/", "io.github.nfsmwrecomp.fake/"), selected="")
    print("PRE729B_SHELL_MOCK_CASES=14_PASS; DEVICE_TESTED=FALSE")
