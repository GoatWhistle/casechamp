import argparse
import json
import resource
import sys
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from time import monotonic
from threading import Lock
from unittest.mock import patch

from run_hypothesis_pilot import fingerprint, prepare, source_hashes, write
from synthetic_traffic import index_paths, index_repair_workers
from synthetic_traffic.incremental import evaluate_incremental
from synthetic_traffic.projects import apply_project


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=60)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    args.output.mkdir(parents=True, exist_ok=False)
    original = root / 'work/network-development/llm-comparison-300s-aligned/automatic-result.json'
    report = json.loads(original.read_text())
    candidates = [row for row in report['index_attempts'] if row['status'] == 'index_timeout']
    selected = min(candidates, key=lambda row: row['after']['vehicle_hours'])
    project = selected['project']
    write(args.output / 'project.json', project)
    stats_lock = Lock()
    stats = defaultdict(lambda: {'calls': 0, 'seconds': 0.0})
    timings = {}
    started = monotonic()
    print(json.dumps({'phase': 'preparing', 'output': str(args.output)}), flush=True)
    prepared = prepare(root, root / 'data/traffic/traffic-8979fdc163fe491a95ca610ed2229033', lambda: None)
    network, _, trips, baseline, _, _, cache = prepared
    timings['preparation_seconds'] = monotonic() - started
    changed = apply_project(network, project)
    started = monotonic()
    after = evaluate_incremental(baseline, changed, iterations=300, tolerance=0.001, deadline=monotonic()+300)
    timings['assignment_seconds'] = monotonic() - started
    if not after.converged:
        raise RuntimeError('Candidate assignment did not converge')
    write(args.output / 'protocol.json', {'source_hashes': source_hashes(root), 'original_result_sha256': fingerprint(original), 'seconds': args.seconds, 'project_sha256': fingerprint(args.output/'project.json')})

    def measured(name, method):
        def call(*positional, **kwargs):
            start = monotonic()
            try:
                return method(*positional, **kwargs)
            finally:
                with stats_lock:
                    stats[name]['calls'] += 1
                    stats[name]['seconds'] += monotonic() - start
        return call

    started = monotonic()
    result = {'baseline': [asdict(v) for v in cache.baseline], 'local_vehicle_hours_before': baseline.assignment.vehicle_hours_per_hour, 'local_vehicle_hours_after': after.vehicle_hours_per_hour}
    print(json.dumps({'phase': 'index', **timings}), flush=True)
    with patch.object(index_repair_workers, 'repair', measured('repair', index_repair_workers.repair)), patch.object(index_paths, 'changes', measured('changes', index_paths.changes)), patch.object(index_paths.DiskTree, 'writable', measured('writable', index_paths.DiskTree.writable)), patch.object(cache, 'values', measured('values', cache.values)), patch.object(cache.network, 'changed', measured('graph', cache.network.changed)):
        try:
            values = cache.evaluate(changed, after.hours, monotonic()+args.seconds)
            result.update(status='verified', after=[asdict(v) for v in values])
        except TimeoutError as error:
            result.update(status='timeout', error=str(error))
    timings['index_seconds'] = monotonic() - started
    result.update(timings=timings, phases=dict(stats), counters=getattr(cache, 'last_evaluation', {}), peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024), phase_note='Concurrent worker durations sum; index_seconds is wall time')
    write(args.output / 'result.json', result)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
