import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path('/Users/andreykuronskin/keys_champ')
LOCAL = Path('/private/tmp/plexus-geography')
for name in ('problem_targets', 'candidate_targets'):
    spec = importlib.util.spec_from_file_location('synthetic_traffic.' + name, LOCAL / 'etl/synthetic_traffic' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
from synthetic_traffic import candidates
from synthetic_traffic.assignment import assign
from synthetic_traffic.demand import aggregate, generate
from synthetic_traffic.housing import distribute
from synthetic_traffic.model import DemandParameters
from synthetic_traffic.source import load_network, load_places

snapshot = ROOT / 'data/traffic/traffic-8979fdc163fe491a95ca610ed2229033'
network = load_network(snapshot)
settlements, _ = load_places(snapshot, network)
homes, _ = distribute(snapshot / 'housing.parquet', settlements, network)
zones, _ = aggregate(homes, network, 2, 128)
trips, _ = generate(network, zones, DemandParameters())
baseline = assign(network, trips, iterations=300, tolerance=.001)
start = time.monotonic()
result = candidates.generate_candidates(network, baseline.flow, baseline.hours, baseline.ratio, limit=16, geography=ROOT / 'data/traffic-geography-hypothesis-pilot/geography.npz', trips=trips, zones=zones, deadline=start+30)
summary = {'seconds': time.monotonic()-start, 'trips':len(trips), 'baseline_converged':baseline.converged, 'diagnostics':result['target_diagnostics'], 'problem_target_ranks':[i for i,row in enumerate(result['target_proposals']) if row.get('target_origin') in {'problem_route','problem_gap'}], 'connection_origins':[row.get('target_origin') for row in result['connections_for_review']], 'connections':len(result['connections_for_review'])}
(LOCAL / 'problem-target-smoke.json').write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
