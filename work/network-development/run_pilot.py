import json
import time
from dataclasses import asdict
from pathlib import Path

from synthetic_traffic.candidates import generate_candidates
from synthetic_traffic.demand import aggregate, generate
from synthetic_traffic.incremental import prepare_incremental
from synthetic_traffic.model import DemandParameters
from synthetic_traffic.search import search_projects
from synthetic_traffic.surrogate import accessibility
from synthetic_traffic.source import load_network, load_places


def main():
    root = Path(__file__).resolve().parents[2]
    path = root / 'data/traffic/traffic-8979fdc163fe491a95ca610ed2229033'
    network = load_network(path)
    places, _ = load_places(path, network)
    zones, _ = aggregate(places, network, 2, 12)
    trips, _ = generate(network, zones, DemandParameters())
    prep = time.monotonic()
    baseline = prepare_incremental(network, trips, 300)
    print(json.dumps({'baseline_seconds': time.monotonic()-prep, 'converged': baseline.assignment.converged}), flush=True)
    start = time.monotonic()
    candidates = generate_candidates(network, baseline.assignment.flow, baseline.assignment.hours,
                                     baseline.assignment.ratio, 32,
                                     geography=root/'data/traffic-geography/geography.json', deadline=start+15)
    print(json.dumps({k:len(v) for k,v in candidates.items() if isinstance(v,list)}),flush=True)
    before_index = accessibility(baseline.assignment, trips, zones)
    result = search_projects(network,trips,candidates,baseline,workers=32,deadline=start+60,
                             iterations=300,zones=zones)
    report = {'snapshot':path.name,'edges':len(network.source),'trips':len(trips),
              'search_seconds':time.monotonic()-start,'evaluated':result.evaluated,
              'capacity_screening':candidates.get('capacity_screening'),
              'stop_reason':result.stop_reason,'objective':'local_accessibility',
              'baseline_index':before_index,'baseline_vehicle_hours':baseline.assignment.vehicle_hours_per_hour,
              'baseline_overloaded_edges':int((baseline.assignment.ratio>1).sum()),
              'candidates':{k:len(v) for k,v in candidates.items() if isinstance(v,list)},
              'results':[{'project':r.project,'gain':r.index_delta,'gain_percent':100*r.index_delta/before_index,
                          'after_index':before_index+r.index_delta,
                          'vehicle_hours_saved':baseline.assignment.vehicle_hours_per_hour-r.after.vehicle_hours_per_hour,
                          'gap':r.after.relative_gap,
                          'overloaded_edges':int((r.after.ratio>1).sum())} for r in result.results]}
    (root/'work/network-development/pilot-no-speed.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in {'results'}}),flush=True)


if __name__ == '__main__':
    main()
