import argparse
from pathlib import Path

from road_traffic.pipeline import run

parser = argparse.ArgumentParser()
parser.add_argument("command", choices=["run"])
parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
parser.add_argument("--output", type=Path)
parser.add_argument("--run-id")
parser.add_argument("--database", default="plexus_traffic")
parser.add_argument("--only", choices=["attributes", "coverage", "observations"])
args = parser.parse_args()
run(
    args.root,
    args.output or args.root / "data/additional/road-traffic/results",
    args.run_id,
    args.database,
    args.only,
)
