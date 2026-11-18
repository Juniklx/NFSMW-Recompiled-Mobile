#!/system/bin/sh
# PRE729: read-only capability probe; not a benchmark or a Perfetto recording.
# Run in Shevery/Shizuku shell, then return to the game during the delay.
# Usage: sh nfsmw_pre729_probe_capture.sh [delay_seconds=20] [report_directory]
set -u
delay=${1:-20}
outdir=${2:-/sdcard/Download}
case "$delay" in ''|*[!0-9]*) echo 'ERRO: atraso deve ser de 0 a 60 segundos'; exit 2;; esac
[ "$delay" -le 60 ] || exit 2
uid=$(id -u)
[ "$uid" = 2000 ] || { echo "ERRO: requer shell Shizuku UID 2000; atual=$uid"; exit 10; }
command -v timeout >/dev/null 2>&1 || { echo 'ERRO: comando timeout indisponivel'; exit 11; }
package=io.github.nfsmwrecomp
version=$(timeout 8 dumpsys package "$package" 2>/dev/null | sed -n 's/.*versionCode=\([0-9][0-9]*\).*/\1/p' | head -n 1)
[ "$version" = 51 ] || { echo "ERRO: sonda exclusiva V51; versionCode=${version:-indisponivel}"; exit 12; }
[ -d "$outdir" ] && [ -w "$outdir" ] || { echo "ERRO: pasta de saida indisponivel: $outdir"; exit 13; }
stamp=$(date +%Y%m%d_%H%M%S)
report="$outdir/NFSMW_PRE729_CAPACIDADE_${stamp}_$$.txt"
# Exclusive creation; never replace an earlier capture.
(set -C; : > "$report") 2>/dev/null || exit 14
echo "PRE729: volte ao jogo e deixe o carro parado. Inicio em ${delay}s."
echo "RELATORIO=$report"
sleep "$delay"

section() {
  echo "BEGIN=$1"
  shift
  timeout 8 "$@" 2>&1
  rc=$?
  echo "COMMAND_RC=$rc"
  echo 'END_SECTION'
}

probe() {
  echo 'PRE729_SCHEMA=1'
  echo 'MODE=READ_ONLY_CAPABILITY_PROBE'
  echo "UID=$uid"
  echo "PACKAGE=$package"
  echo "VERSION_CODE=$version"
  echo "DELAY_SECONDS=$delay"
  echo 'DEVICE_CAPTURE_VALIDATED=FALSE'
  echo 'CLOCK_ALIGNMENT_ESTABLISHED=FALSE'
  echo 'FPS_GAIN_MEASURED=FALSE'
  section DATE_BEGIN date +%s
  section UPTIME_BEGIN cat /proc/uptime
  section PERFETTO_VERSION perfetto --version
  section PERFETTO_SERVICE perfetto --query
  section ATRACE_CATEGORIES atrace --list_categories
  section THERMAL_BEGIN dumpsys thermalservice
  # Filter to this game's SurfaceView; never silently select a UI/VRI layer.
  layers=$(timeout 8 dumpsys SurfaceFlinger --list 2>&1)
  list_rc=$?
  candidates=$(printf '%s\n' "$layers" | awk 'index($0,"SurfaceView") && index($0,"io.github.nfsmwrecomp")')
  count=$(printf '%s\n' "$candidates" | awk 'NF {n++} END {print n+0}')
  echo "SURFACE_LIST_RC=$list_rc"
  echo "SURFACE_CANDIDATES=$count"
  printf '%s\n' "$candidates"
  if [ "$list_rc" = 0 ] && [ "$count" = 1 ]; then
    i=1
    while [ "$i" -le 3 ]; do
      echo "BEGIN=LATENCY_$i"
      date +%s
      cat /proc/uptime
      raw=$(timeout 8 dumpsys SurfaceFlinger --latency "$candidates" 2>&1)
      rc=$?
      printf '%s\n' "$raw"
      valid=$(printf '%s\n' "$raw" | awk 'NF==3 && $1 ~ /^[0-9]+$/ && $2 ~ /^[0-9]+$/ && $3 ~ /^[0-9]+$/ && $1>0 && $2>0 && $3>0 && $1!="9223372036854775807" && $2!="9223372036854775807" && $3!="9223372036854775807" {n++} END {print n+0}')
      echo "LATENCY_RC=$rc"
      echo "VALID_TRIPLE_ROWS=$valid"
      echo 'END_SECTION'
      [ "$i" = 3 ] || sleep 1
      i=$((i+1))
    done
  else
    echo 'LATENCY_SKIPPED=NO_UNIQUE_GAME_SURFACE'
  fi
  section THERMAL_END dumpsys thermalservice
  section DATE_END date +%s
  section UPTIME_END cat /proc/uptime
  echo 'STATUS=PRE729_CAPABILITY_RECORDED_REQUIRES_ANALYSIS'
  echo 'NOTE=Successful commands alone do not prove usable traces or frame identity.'
}
probe > "$report" 2>&1
rc=$?
echo "PRE729_PROBE_RC=$rc"
echo "RELATORIO=$report"
echo 'Envie o TXT gerado. Nenhuma configuracao do jogo foi alterada.'
exit "$rc"
