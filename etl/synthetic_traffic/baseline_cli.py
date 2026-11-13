import argparse
import json
from dataclasses import asdict
from hashlib import file_digest
from pathlib import Path

from synthetic_traffic.baseline_store import save_baseline
from synthetic_traffic.demand import aggregate, generate
from synthetic_traffic.demand_store import load_demand, save_demand
from synthetic_traffic.housing import distribute
from synthetic_traffic.incremental import prepare_incremental
from synthetic_traffic.initial_flow_checkpoint import read_initial_flows
from synthetic_traffic.model import DemandParameters
from synthetic_traffic.load_preview import save_preview
from synthetic_traffic.source import load_network, load_places


def demand_progress(done: int, total: int) -> None:
    if done % 25 == 0 or done == total:
        print(json.dumps({'stage': 'demand', 'completed': done, 'total': total}), flush=True)


def assignment_progress(value: dict) -> None:
    done = value.get('completed', 0)
    if not done or done % 25 == 0 or done == value.get('total'):
        print(json.dumps(value), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--prepare-demand-only', type=Path)
    parser.add_argument('--load-demand', type=Path)
    parser.add_argument('--tree-cache', type=Path)
    parser.add_argument('--initial-flow-checkpoint', type=Path)
    parser.add_argument('--region', action='append')
    parser.add_argument('--region-id', action='append')
    parser.add_argument('--settlement-zones', action='store_true')
    parser.add_argument('--homes', type=Path)
    parser.add_argument('--cell-km', type=float, default=10)
    parser.add_argument('--max-zones', type=int, default=128)
    parser.add_argument('--iterations', type=int, default=10000)
    parser.add_argument('--tolerance', type=float, default=0.001)
    parser.add_argument('--preview-on-limit', action='store_true')
    args = parser.parse_args()
    if bool(args.region) != bool(args.region_id) or len(args.region or []) != len(args.region_id or []):
        parser.error('Supply matching --region and --region-id entries')
    if args.output.exists():
        raise FileExistsError(args.output)
    source = json.loads((args.snapshot / 'source.json').read_text())
    for name, expected in source['sha256'].items():
        with (args.snapshot / name).open('rb') as stream:
            if file_digest(stream, 'sha256').hexdigest() != expected:
                raise ValueError(f'Snapshot checksum mismatch: {name}')
    print(json.dumps({'stage': 'loading_network'}), flush=True)
    graph = load_network(args.snapshot)
    parameters = DemandParameters()
    if args.load_demand:
        trips, metadata = load_demand(args.load_demand, source, parameters, args.region_id)
        zones = metadata['zones']
    else:
        places, coverage = load_places(args.snapshot, graph, args.region)
        metadata = {'source': source, 'coverage': coverage, 'region_ids': args.region_id}
        if args.homes:
            places, housing = distribute(args.homes, places, graph)
            metadata['housing'] = housing
        zones, cell = (places, None) if args.settlement_zones else aggregate(places, graph, args.cell_km, args.max_zones)
        print(json.dumps({'stage': 'demand', 'zones': len(zones)}), flush=True)
        trips, demand = generate(graph, zones, parameters, demand_progress)
        if not trips:
            raise ValueError('No interzonal demand generated')
        metadata.update(parameters=asdict(parameters), demand=demand, effective_cell_km=cell,
                        zones=[asdict(zone) for zone in zones])
    if args.prepare_demand_only:
        save_demand(args.prepare_demand_only, trips, metadata)
        print(json.dumps({'stage': 'demand_saved', 'path': str(args.prepare_demand_only),
                          'trips': len(trips)}), flush=True)
        return
    print(json.dumps({'stage': 'assignment', 'nodes': len(graph.raw_nodes),
                      'edges': len(graph.source), 'zones': len(zones), 'trips': len(trips)}), flush=True)
    initial_flows = None
    if args.initial_flow_checkpoint:
        if args.load_demand is None or args.tree_cache is None:
            raise ValueError('Initial flow resume requires saved demand and a tree cache')
        demand_record = json.loads((args.load_demand / 'demand.json').read_text())
        initial_flows = read_initial_flows(args.initial_flow_checkpoint, source, demand_record['sha256'])
        print(json.dumps({'stage': 'resuming_initial_flows', 'origins': len(initial_flows)}), flush=True)
    baseline = prepare_incremental(graph, trips, args.iterations, args.tolerance, tree_directory=args.tree_cache, path_limit=parameters.max_trip_hours, progress=assignment_progress, initial_flows=initial_flows)
    if not baseline.assignment.converged and args.preview_on_limit:
        save_preview(args.output, args.snapshot, baseline.assignment.flow,
            baseline.assignment.relative_gap, metadata,
            {'iteration': baseline.assignment.iterations,
             'unserved_vehicles_per_hour': baseline.assignment.unserved_vehicles_per_hour,
             'gap_basis': 'same_assignment_flow_and_loaded_shortest_paths',
             'routing_scenarios_ready': False})
    else:
        save_baseline(baseline, args.output, metadata)
    print(json.dumps({'stage': 'published', 'baseline': str(args.output),
                      'relative_gap': baseline.assignment.relative_gap,
                      'iterations': baseline.assignment.iterations,
                      'converged': baseline.assignment.converged}), flush=True)


if __name__ == '__main__':
    main()
