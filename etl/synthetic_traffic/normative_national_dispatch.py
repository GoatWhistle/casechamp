import argparse
import fcntl
import hashlib
import json
import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from synthetic_traffic.normative_city_boundaries import (
    municipal_boundary_counts,
    prepare_city_boundaries,
)
from synthetic_traffic.normative_national_archive import archive_region
from synthetic_traffic.normative_national_pipeline import ORDER, NationalPipeline

ROAD = ("N01", "N02", "N03", "N05", "N06", "N07", "N08")
WALK = ("N04", "N09")
EXPECTED = {*(name + "_federal_district" for name in ORDER), "crimea"}


class NationalDispatch:
    def __init__(self, repo, api):
        self.repo, self.api = Path(repo).resolve(), api
        self.root = self.repo / ".local/normative-national-inputs"
        self.path = self.root / "dispatch-state.json"
        self.state = (
            json.loads(self.path.read_text()) if self.path.exists() else {"regions": {}}
        )
        self.state.update({"pid": os.getpid(), "api": api})
        self.runner = NationalPipeline(self.repo)

    def save(self, status, **fields):
        self.state.update(
            {"status": status, "updated_at": datetime.now(UTC).isoformat(), **fields}
        )
        temporary = self.path.with_suffix(".json.part")
        temporary.write_text(json.dumps(self.state, indent=2))
        temporary.replace(self.path)
        print(json.dumps({"status": status, **fields}), flush=True)

    def wait_sources(self, stage):
        while True:
            self.runner.guard()
            source = json.loads((self.root / "pipeline-state.json").read_text())
            rows = source.get("sources", {})
            ready = [
                key for key in EXPECTED if rows.get(key, {}).get(stage) == "complete"
            ]
            self.save(
                "waiting_" + stage,
                ready_sources=len(ready),
                expected_sources=len(EXPECTED),
            )
            if len(ready) == len(EXPECTED):
                return
            if source.get("status") == "finished_current_pass":
                attempts = self.state.get("data_retry_passes", 0)
                if attempts >= 3:
                    raise RuntimeError(
                        "National source pass remains incomplete after three retry passes"
                    )
                self.state["data_retry_passes"] = attempts + 1
                self.save("retrying_incomplete_sources")
                self.runner.command(
                    "synthetic_traffic.normative_national_pipeline",
                    "--repo",
                    self.repo,
                    "--env",
                    self.repo / ".env.analytics",
                    "--reuse-external-cache",
                    self.root / "osm",
                    "--walking-raw",
                )
            else:
                time.sleep(10)

    def wait_calculators(self):
        while True:
            self.runner.guard()
            lines = subprocess.check_output(
                ["ps", "-axo", "pid,args"], text=True
            ).splitlines()
            busy = [
                line
                for line in lines
                if "calculate_regional_measurements" in line
                and "normative_national_dispatch" not in line
            ]
            if not busy:
                return
            self.save("waiting_existing_measurement_batch")
            time.sleep(10)

    def calculate(self, regions, criteria, output):
        self.wait_calculators()
        self.runner.command(
            "calculate_regional_measurements",
            "--api",
            self.api,
            "--regions",
            regions,
            "--output",
            output,
            "--criteria",
            *criteria,
        )
        records = json.loads(Path(output).read_text())
        return {
            "successful": sum(row["status"] == 200 for row in records),
            "cases": len(records),
            "incomplete": [row for row in records if row["status"] != 200],
        }

    def export(self, regions, criteria):
        self.runner.command(
            "aggregate_municipal_measurements",
            "--output",
            self.repo / "datasets/municipal-indices",
            "--regions",
            *regions,
            "--criteria",
            *criteria,
            "--export",
            self.repo / "datasets/municipal-indices/municipal-indices.jsonl.gz",
        )

    def run(self):
        self.wait_sources("poi_import")
        sources = json.loads((self.root / "osm/manifest.json").read_text())
        fingerprint = hashlib.sha256(
            json.dumps(
                [(row["id"], row["sha256"]) for row in sources], sort_keys=True
            ).encode()
        ).hexdigest()
        if self.state.get("source_fingerprint") != fingerprint:
            self.state = {
                "regions": {},
                "pid": os.getpid(),
                "api": self.api,
                "source_fingerprint": fingerprint,
            }
        self.save("preparing_city_municipal_boundaries")
        self.state["city_boundaries"] = prepare_city_boundaries(self.repo)
        self.state["municipal_boundary_counts"] = municipal_boundary_counts()
        regions = json.loads((self.root / "regions.json").read_text())["regions"]
        if not self.state.get("road_batch_finished"):
            self.save("calculating_national_road_measurements")
            self.state["road_result"] = self.calculate(
                self.root / "regions.json", ROAD, self.root / "road-measurements.json"
            )
            self.export([row["id"] for row in regions], ROAD)
            self.state["road_batch_finished"] = True
            self.save("road_pass_complete")
        self.wait_sources("walking_raw")
        priority = {"32000000": 0, "07000000": 1, "35000000": 2}
        regions.sort(key=lambda row: (priority.get(row["id"], 3), row["id"]))
        for region in regions:
            identifier = region["id"]
            result = self.state["regions"].setdefault(identifier, {})
            if result.get("status") == "complete":
                continue
            try:
                if not self.state["municipal_boundary_counts"].get(identifier):
                    result.update(
                        {
                            "status": "missing_municipal_geometry",
                            "error": "No source municipal polygons imported",
                        }
                    )
                    self.save("region_missing_geometry", current_region=identifier)
                    continue
                self.wait_calculators()
                self.save("assembling_regional_pedestrian", current_region=identifier)
                self.runner.guard(1024**3)
                self.runner.command(
                    "assemble_regional_walking",
                    "--region-id",
                    identifier,
                    "--import-storage",
                )
                result["archive"] = archive_region(self.repo, identifier)
                self.save("calculating_regional_walking", current_region=identifier)
                region_path = self.root / (identifier + ".regions.json")
                region_path.write_text(
                    json.dumps({"regions": [region]}, ensure_ascii=False)
                )
                result["measurement"] = self.calculate(
                    region_path,
                    WALK,
                    self.root / (identifier + ".walking-measurements.json"),
                )
                self.export([identifier], WALK)
                road_incomplete = any(
                    row["region_id"] == identifier
                    for row in self.state["road_result"]["incomplete"]
                )
                result["status"] = (
                    "complete"
                    if not result["measurement"]["incomplete"] and not road_incomplete
                    else "partial"
                )
                self.save("region_pass_finished", current_region=identifier)
            except (
                OSError,
                ValueError,
                RuntimeError,
                subprocess.SubprocessError,
            ) as error:
                result.update(
                    {"status": "failed", "error": f"{type(error).__name__}: {error}"}
                )
                self.save(
                    "region_failed", current_region=identifier, error=result["error"]
                )
                if "guard" in str(error) or (self.root / "STOP").exists():
                    return
        self.save(
            "finished_current_pass",
            current_region=None,
            completed_regions=sum(
                row.get("status") == "complete"
                for row in self.state["regions"].values()
            ),
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--api", default="http://127.0.0.1:8007/api/v1")
    parser.add_argument("--env", type=Path, required=True)
    args = parser.parse_args()
    for line in args.env.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip().strip("\"'")
    dispatch = NationalDispatch(args.repo, args.api)
    try:
        with (dispatch.root / ".dispatch.lock").open("a+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            dispatch.run()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        dispatch.save("failed", error=f"{type(error).__name__}: {error}")
        raise


if __name__ == "__main__":
    main()
