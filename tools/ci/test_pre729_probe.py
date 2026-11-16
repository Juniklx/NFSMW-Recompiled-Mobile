#!/usr/bin/env python3
"""Mock shell tests for PRE729 guardrails. These are not device measurements."""
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/diagnostics/nfsmw_pre729_probe_capture.sh"
MOCK = '''#!/bin/sh
name=${0##*/}
printf '%s %s\\n' "$name" "$*" >> "$TEST_CALLS"
case "$name" in
 id) echo "$TEST_UID";;
 sleep) :;;
 perfetto) [ "$TEST_PERFETTO_RC" = 0 ] || exit "$TEST_PERFETTO_RC"; echo 'linux.ftrace available';;
 atrace) echo 'gfx - Graphics';;
 dumpsys)
  case "$1" in
   package) echo "versionCode=$TEST_VERSION minSdk=26";;
   thermalservice) echo 'Thermal Status: 0'; echo 'IsStatusOverride: false';;
   SurfaceFlinger)
    if [ "$2" = --list ]; then
     i=0
     while [ "$i" -lt "$TEST_LAYERS" ]; do
      echo "SurfaceView[io.github.nfsmwrecomp/GameActivity]#$i"
      i=$((i+1))
     done
    elif [ "$2" = --latency ]; then
     echo 8333333
     echo '1000000000 1000000001 1000000002'
     echo '0 0 0'
     echo '2000000000 9223372036854775807 2000000002'
    else exit 98; fi;;
   *) exit 99;;
  esac;;
esac
'''

def case(uid="2000", version="51", layers="1", perfetto_rc="0", expected=0):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        bindir = root / "bin"
        bindir.mkdir()
        for name in ("id", "sleep", "perfetto", "atrace", "dumpsys"):
            p = bindir / name
            p.write_text(MOCK)
            p.chmod(0o755)
        env = dict(os.environ, PATH=str(bindir) + os.pathsep + os.environ["PATH"],
                   TEST_CALLS=str(root / "calls"), TEST_UID=uid, TEST_VERSION=version,
                   TEST_LAYERS=layers, TEST_PERFETTO_RC=perfetto_rc)
        result = subprocess.run(["sh", str(SCRIPT), "0", str(root)], env=env,
                                capture_output=True, text=True, timeout=10)
        assert result.returncode == expected, result.stdout + result.stderr
        files = list(root.glob("NFSMW_PRE729_CAPACIDADE_*.txt"))
        if expected:
            assert not files, "A rejected UID/version must not collect a report"
        else:
            assert len(files) == 1
            text = files[0].read_text()
            assert "PRE729_CAPABILITY_RECORDED_REQUIRES_ANALYSIS" in text
            if layers == "1":
                assert text.count("VALID_TRIPLE_ROWS=1") == 3, text
            else:
                assert "LATENCY_SKIPPED=NO_UNIQUE_GAME_SURFACE" in text
                assert "BEGIN=LATENCY_" not in text
            if perfetto_rc != "0":
                assert "COMMAND_RC=" + perfetto_rc in text
        calls = (root / "calls").read_text()
        assert "--latency-clear" not in calls and "--timestats" not in calls
        assert "override-status" not in calls
        for line in calls.splitlines():
            if line.startswith("perfetto "):
                assert line in ("perfetto --version", "perfetto --query")

if __name__ == "__main__":
    subprocess.run(["sh", "-n", str(SCRIPT)], check=True)
    case()
    case(uid="10000", expected=10)
    case(version="52", expected=12)
    case(layers="0")
    case(layers="2")
    case(perfetto_rc="124")
    print("PRE729_SHELL_MOCK_CASES=6_PASS; DEVICE_TESTED=FALSE")
