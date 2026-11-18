"""Run with Python 3: analyze_pre730b.py ARCHIVE TRACE_PROCESSOR_SHELL."""
import bisect
import csv
import io
import json
import re
import subprocess
import sys
import tarfile
import tempfile
from collections import Counter
from pathlib import Path


def analyze(archive, processor, tmp):
    with tarfile.open(archive, 'r:gz') as tar:
        def read_member(name, limit):
            matches = [m for m in tar if m.isfile() and Path(m.name).name == name]
            if len(matches) != 1 or matches[0].size > limit:
                raise ValueError(f'Unexpected member: {name}')
            return tar.extractfile(matches[0]).read()
        report = read_member('coleta.txt', 8 << 20).decode()
        trace = tmp / 'trace.pftrace'
        trace.write_bytes(read_member('trace.pftrace', 128 << 20))
    assert re.search(r'^PERFETTO_RC=0$', report, re.M) and trace.stat().st_size
    rows = set()
    edges = set()
    samples = 0
    periods = set()
    for block in re.findall(r'BEGIN_SAMPLE=\d+\n(.*?)END_SAMPLE', report, re.S):
        if 'LATENCY_RC=0\n' not in block:
            continue
        samples += 1
        periods.update(map(int, re.findall(r'^([0-9]+)$', block, re.M)))
        sample = []
        for row in re.findall(r'^(\d+)[ \t]+(\d+)[ \t]+(\d+)$', block, re.M):
            values = tuple(map(int, row))
            if all(0 < x < 2**63-1 for x in values):
                sample.append(values)
        # Only intervals actually adjacent in a read can enter an FPS estimate.
        rows.update(sample)
        edges.update((a[1], b[1]) for a, b in zip(sample, sample[1:]) if b[1] > a[1])
    assert len(periods) == 1
    period = periods.pop()
    ordered = sorted(rows, key=lambda x: x[1])
    assert len(ordered) == len({x[1] for x in ordered}) and len(ordered)>1

    def query(sql):
        result = subprocess.run([processor, trace, '-Q', sql], capture_output=True,
                                text=True, check=True)
        return list(csv.DictReader(io.StringIO(result.stdout)))

    offsets = query("select distinct ts-clock_value off from clock_snapshot where clock_name='MONOTONIC'")
    measured = sorted(int(x['off']) for x in offsets)
    if not measured or measured[-1] - measured[0] > 1000:
        raise ValueError('Inspect clock drift or missing clock snapshots before matching')
    low, high = measured[0], measured[-1]
    offset = (low + high) // 2
    bounds = query('select * from trace_bounds')[0]
    display = query("""select a.ts+a.dur t, a.jank_type j from actual_frame_timeline_slice a
      join process p using(upid) where p.name='/system/bin/surfaceflinger'
      and surface_frame_token is null and a.present_type != 'Dropped Frame' and a.dur>0 order by t""")
    times = [int(d['t']) for d in display]
    counts, match, used = Counter(), Counter(), set()
    eligible = max_error = 0
    observed_ns = 0
    for prev, cur in zip(ordered, ordered[1:]):
        if (prev[1], cur[1]) not in edges:
            continue
        observed_ns += cur[1] - prev[1]
        cycles = tuple(round((b-a)/period) for a,b in zip(prev,cur))
        counts[cycles] += 1
        t = cur[1]+offset
        if prev[1]+low < int(bounds['start_ts']) or cur[1]+high > int(bounds['end_ts']):
            continue
        eligible += 1
        candidates = range(bisect.bisect_left(times,cur[1]+low-100_000),bisect.bisect_right(times,cur[1]+high+100_000))
        if len(candidates) != 1 or candidates[0] in used:
            continue
        # Require the same accepted display match for both measured offsets.
        if max(abs(cur[1]+d-times[candidates[0]]) for d in (low, high)) <= 100_000:
            i = candidates[0]
            used.add(i)
            max_error = max(max_error,abs(times[i]-t))
            match[cycles[1],display[i]['j']] += 1
    span = (ordered[-1][1]-ordered[0][1])/1e9
    return dict(samples=samples, period_ns=period, unique=len(rows), span_s=span,
                observed_span_s=observed_ns/1e9, intervals=sum(counts.values()),
                unobserved_joins=len(rows)-1-sum(counts.values()),
                clock_offset_range_ns=[low,high],
                presentations_per_second=sum(counts.values())*1e9/observed_ns,
                desired_actual_ready_cycles={str(k):v for k,v in sorted(counts.items())},
                mono_to_boot_ns=offset, eligible=eligible, matched=len(used),
                max_error_ns=max_error, display_classes={str(k):v for k,v in sorted(match.items())},
                trace_stats=query("""select name,idx,value,severity from stats where value>0 and
                    (severity in ('error','data_loss') or name in ('traced_buf_bytes_overwritten',
                    'traced_buf_chunks_overwritten','traced_chunks_discarded'))"""))


if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as directory:
        print(json.dumps(analyze(sys.argv[1],sys.argv[2],Path(directory)),indent=2))
