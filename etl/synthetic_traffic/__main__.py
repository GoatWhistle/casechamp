import argparse
import json
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from synthetic_traffic.baseline_store import save_baseline
from synthetic_traffic.collection import collect
from synthetic_traffic.demand import aggregate, generate
from synthetic_traffic.housing import distribute
from synthetic_traffic.housing_extract import extract
from synthetic_traffic.incremental import prepare_incremental
from synthetic_traffic.model import DemandParameters, Trip
from synthetic_traffic.publish import publish_homes, publish_run
from synthetic_traffic.report import compare
from synthetic_traffic.snapshot import export_snapshot
from synthetic_traffic.source import load_network, load_places


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    publish = commands.add_parser("publish")
    publish.add_argument("--homes", type=Path)
    publish.add_argument("--run", type=Path)
    publish.add_argument("--snapshot", type=Path)
    publish.add_argument("--run-id")
    collection = commands.add_parser("collect-homes")
    collection.add_argument("--output", type=Path, required=True)
    snapshot = commands.add_parser("snapshot")
    snapshot.add_argument("--output", type=Path, required=True)
    snapshot.add_argument("--bbox", type=float, nargs=4)
    homes = commands.add_parser("homes")
    homes.add_argument("--pbf", type=Path, required=True)
    homes.add_argument("--output", type=Path, required=True)
    run = commands.add_parser("run")
    run.add_argument("--snapshot", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--region")
    run.add_argument("--homes", type=Path)
    run.add_argument("--pair", nargs=2)
    run.add_argument("--pair-flow", type=float, default=1000.0)
    run.add_argument("--projects", type=Path)
    run.add_argument("--demand-parameters", type=Path)
    run.add_argument("--cell-km", type=float, default=10.0)
    run.add_argument("--max-zones", type=int, default=32)
    run.add_argument("--iterations", type=int, default=100)
    run.add_argument("--tolerance", type=float, default=0.001)
    run.add_argument("--duration-hours", type=float, default=1.0)
    run.add_argument("--multipliers", type=float, nargs="+", default=[0.7, 1.0, 1.3])
    baseline_parser = commands.add_parser("baseline", parents=[run], add_help=False)
    baseline_parser.set_defaults(command="baseline")
    args = parser.parse_args()
    if args.command == "publish":
        if args.homes:
            print(json.dumps(publish_homes(args.homes), indent=2))
        if args.run:
            if not args.snapshot or not args.run_id:
                raise ValueError("Publishing a run requires snapshot and run-id")
            print(
                json.dumps(publish_run(args.run, args.snapshot, args.run_id), indent=2)
            )
        if not args.homes and not args.run:
            raise ValueError("Specify homes and/or a run to publish")
        return
    if args.command == "collect-homes":
        collect(args.output)
        return
    if args.command == "snapshot":
        export_snapshot(args.output, args.bbox)
        return
    if args.command == "homes":
        print(json.dumps(extract(args.pbf, args.output), indent=2))
        return
    network = load_network(args.snapshot)
    places, coverage = load_places(args.snapshot, network, args.region)
    metadata = {
        "source": json.loads((args.snapshot / "source.json").read_text()),
        "coverage": coverage,
    }
    if args.pair:
        selected = [
            next((z for z in places if z.id == identifier), None)
            for identifier in args.pair
        ]
        if any(z is None for z in selected):
            raise ValueError(
                "Pair identifiers must occur among populated road-bound origins"
            )
        a, b = selected
        assert a is not None and b is not None
        trips = [Trip(a.node, b.node, args.pair_flow)]
        metadata.update(
            scope="pair_single_direction", background="none", pair=args.pair
        )
    else:
        if args.homes:
            places, housing = distribute(args.homes, places, network)
            metadata["housing"] = {
                **housing,
                "sha256": (
                    {
                        p.name: sha256(p.read_bytes()).hexdigest()
                        for p in sorted(args.homes.glob("*.parquet"))
                    }
                    if args.homes.is_dir()
                    else sha256(args.homes.read_bytes()).hexdigest()
                ),
            }
        zones, cell = aggregate(places, network, args.cell_km, args.max_zones)
        parameters = (
            DemandParameters(**json.loads(args.demand_parameters.read_text()))
            if args.demand_parameters
            else DemandParameters()
        )
        trips, demand = generate(network, zones, parameters)
        metadata.update(
            scope="region" if args.region else "all_snapshot_population",
            zones=len(zones),
            effective_cell_km=cell,
            parameters=asdict(parameters),
            demand=demand,
            zone_population=[asdict(z) for z in zones],
        )
    if not trips:
        raise ValueError(
            "No interzonal demand generated; refine zones or inspect disconnected origins"
        )
    if args.command == "baseline":
        baseline = prepare_incremental(network, trips, args.iterations, args.tolerance)
        save_baseline(baseline, args.output, metadata)
        print(json.dumps({"baseline": str(args.output), "converged": baseline.assignment.converged,
                          "relative_gap": baseline.assignment.relative_gap, "trips": len(trips)}))
        return
    projects = json.loads(args.projects.read_text()) if args.projects else []
    if not isinstance(projects, list) or any(not isinstance(p, dict) for p in projects):
        raise ValueError(
            "Projects must be a JSON array of capacity or closure changes"
        )
    result = compare(
        network,
        trips,
        projects,
        args.output,
        args.duration_hours,
        args.iterations,
        args.tolerance,
        metadata,
        args.multipliers,
    )
    print(
        json.dumps(
            {
                "report": str(args.output / "report.json"),
                "demand_sha256": result["demand_sha256"],
                "converged_baselines": sum(
                    c["baseline"]["converged"] for c in result["cases"]
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
