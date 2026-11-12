import argparse
import json
from pathlib import Path

from synthetic_traffic.geography_queue_plan import plan
from synthetic_traffic.geography_queue_store import status
from synthetic_traffic.geography_queue_worker import run_queue
from synthetic_traffic.geography_tile import fetch_tile


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Durable geography acquisition for supplied atlas regions"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    planning = commands.add_parser("plan")
    planning.add_argument("--boundaries", required=True, type=Path)
    planning.add_argument("--output", required=True, type=Path)
    planning.add_argument(
        "--priority-bbox",
        type=float,
        nargs=4,
        metavar=("WEST", "SOUTH", "EAST", "NORTH"),
    )
    running = commands.add_parser("run")
    running.add_argument("--output", required=True, type=Path)
    running.add_argument("--vector-cache", type=Path)
    showing = commands.add_parser("status")
    showing.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args(argv)
    if arguments.command == "plan":
        result = plan(arguments.boundaries, arguments.output, arguments.priority_bbox)
    elif arguments.command == "run":
        result = run_queue(arguments.output, fetch_tile, arguments.vector_cache)
    else:
        result = status(arguments.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
