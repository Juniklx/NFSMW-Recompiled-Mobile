#!/system/bin/sh
# Captura curta da V51: SurfaceFlinger e Perfetto na mesma janela.
set -eu
pkg=io.github.nfsmwrecomp
[ "$(id -u)" = 2000 ] || { echo 'Execute no shell do Shevery.'; exit 1; }
ver=$(timeout 8 dumpsys package "$pkg" | sed -n 's/.*versionCode=\([0-9][0-9]*\).*/\1/p' | head -1)
[ "$ver" = 51 ] || { echo "Versao encontrada: ${ver:-indisponivel}"; exit 1; }
out=/sdcard/Download
name=NFSMW_PRE730_$(date +%Y%m%d_%H%M%S)_$$
dir="$out/$name"
mkdir "$dir"
report="$dir/coleta.txt"
echo "PRE730 V51. Volte ao jogo em 20 segundos. Pasta: $dir"
sleep 20
layers=$(timeout 8 dumpsys SurfaceFlinger --list)
layer=$(printf '%s\n' "$layers" | awk '
index($0,"SurfaceView[io.github.nfsmwrecomp/") && index($0,"(BLAST)") && !/ !handle/ {
 n=$0
 if(sub(/^RequestedLayerState\{/,"",n)){sub(/ (parentId=|relativeParentId=|mirrorId=|z=|layerStack=).*/,"",n);sub(/\}$/,"",n)}
 if(n !~ /^Background for / && !seen[n]++) {count++; selected=n}
} END {if(count==1) print selected}')
printf 'VERSION=%s\nLAYER=%s\n' "$ver" "$layer" > "$report"
[ -n "$layer" ] || { echo "Camada BLAST ausente ou ambigua. Envie $report"; exit 1; }
thermal() { timeout 5 dumpsys thermalservice >> "$report" 2>&1 || echo "THERMAL_RC=$?" >> "$report"; }
thermal
cat > "$dir/config.pbtxt" <<'CFG'
duration_ms: 20000
buffers { size_kb: 32768 fill_policy: RING_BUFFER }
buffers { size_kb: 4096 fill_policy: RING_BUFFER }
data_sources { config { name: "android.surfaceflinger.frametimeline" target_buffer: 1 } }
data_sources { config { name: "linux.process_stats" target_buffer: 1 process_stats_config { scan_all_processes_on_start: true } } }
data_sources { config { name: "linux.ftrace" ftrace_config {
 ftrace_events: "sched/sched_switch"
 ftrace_events: "sched/sched_waking"
 ftrace_events: "power/cpu_frequency"
 atrace_categories: "gfx"
} } }
CFG
timeout 35 perfetto --txt -c - -o - < "$dir/config.pbtxt" > "$dir/trace.pftrace" 2> "$dir/perfetto.txt" &
worker=$!
i=0
while kill -0 "$worker" 2>/dev/null && [ "$i" -lt 35 ]; do
  {
    echo "BEGIN_SAMPLE=$i"
    cat /proc/uptime
    rc=0
    timeout 3 dumpsys SurfaceFlinger --latency "$layer" || rc=$?
    echo "LATENCY_RC=$rc"
    cat /proc/uptime
    echo END_SAMPLE
  } >> "$report" 2>&1
  i=$((i+1))
  sleep 1
done
rc=0
wait "$worker" || rc=$?
echo "PERFETTO_RC=$rc" >> "$report"
thermal
bytes=$(wc -c < "$dir/trace.pftrace")
echo "TRACE_BYTES=$bytes" >> "$report"
if tar -czf "$dir.tar.gz.part" -C "$out" "$name" && mv "$dir.tar.gz.part" "$dir.tar.gz"; then
  echo "Envie $dir.tar.gz"
else
  echo "Envie os arquivos da pasta $dir"
  exit 1
fi
[ "$rc" = 0 ] && [ "$bytes" -gt 0 ] || { echo 'Perfetto falhou. O pacote inclui o diagnostico.'; exit 1; }
