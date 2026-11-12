import argparse
import fcntl
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen

import acquire_normative_national as acquisition
from synthetic_traffic.normative_national_sources import seed_existing

GIB = 1024**3
BASE = "https://download.openstreetmap.fr/extracts/russia/"
ORDER = (
    "siberian",
    "central",
    "volga",
    "northwestern",
    "far_eastern",
    "north_caucasian",
    "southern",
    "ural",
)


class NationalPipeline:
    def __init__(self, repo, minimum_free_gib=15, walking_raw=False):
        self.repo = Path(repo).resolve()
        self.root = self.repo / ".local/normative-national-inputs"
        self.root.mkdir(parents=True, exist_ok=True)
        self.minimum_free = minimum_free_gib * GIB
        self.walking_raw = walking_raw
        self.state_path = self.root / "pipeline-state.json"
        self.state = (
            json.loads(self.state_path.read_text())
            if self.state_path.exists()
            else {"sources": {}}
        )
        self.state.update(
            {
                "pid": os.getpid(),
                "minimum_free_gib": minimum_free_gib,
                "walking_raw_requested": walking_raw,
            }
        )
        acquisition.ROOT = self.root / "osm"
        acquisition.download = self.download

    def save(self, status, **fields):
        self.state.update(
            {"status": status, "updated_at": datetime.now(UTC).isoformat(), **fields}
        )
        temporary = self.state_path.with_suffix(".json.part")
        temporary.write_text(json.dumps(self.state, indent=2))
        temporary.replace(self.state_path)
        print(json.dumps({"status": status, **fields}), flush=True)

    def guard(self, reserve=0):
        if (self.root / "STOP").exists():
            raise RuntimeError("Stop requested through the national pipeline STOP file")
        free = shutil.disk_usage(self.root).free
        if free < self.minimum_free + reserve:
            raise RuntimeError(
                "Disk guard: retain minimum free space before this stage"
            )

    def download(self, url, path):
        self.guard()
        with urlopen(
            Request(url, headers={"User-Agent": "Plexus-national-accessibility/1.0"}),
            timeout=120,
        ) as response:
            expected = response.headers.get("Content-Length")
            expected = int(expected) if expected else None
            self.guard(expected or 0)
            total = 0
            with Path(path).open("wb") as target:
                while block := response.read(4 * 1024 * 1024):
                    self.guard()
                    target.write(block)
                    total += len(block)
                    if total % (32 * 1024 * 1024) == 0:
                        self.save(
                            "downloading",
                            download_bytes=total,
                            download_expected_bytes=expected,
                        )
            if expected is not None and total != expected:
                raise ValueError("Downloaded national source is truncated")

    def command(self, module, *arguments):
        self.guard()
        process = subprocess.Popen(
            [sys.executable, "-m", module, *map(str, arguments)], cwd=self.repo
        )
        try:
            while process.poll() is None:
                self.guard()
                try:
                    rss = (
                        int(
                            subprocess.check_output(
                                ["ps", "-p", str(process.pid), "-o", "rss="], text=True
                            ).strip()
                            or 0
                        )
                        * 1024
                    )
                    if rss > 4 * GIB:
                        raise RuntimeError(
                            "Memory guard: one extraction worker exceeded 4 GiB RSS"
                        )
                except subprocess.CalledProcessError:
                    pass
                time.sleep(2)
            if process.returncode:
                raise RuntimeError(
                    f"{module} failed with exit code {process.returncode}"
                )
        except BaseException:
            process.terminate()
            process.wait()
            raise

    def run(self):
        self.save("running")
        for key in [*(short + "_federal_district" for short in ORDER), "crimea"]:
            stages = self.state["sources"].setdefault(key, {})
            try:
                self.guard()
                self.save("acquiring", current_source=key)
                acquisition.SOURCES = [(key, BASE)]
                acquisition.main()
                source = next(
                    row
                    for row in json.loads((self.root / "osm/manifest.json").read_text())
                    if row["id"] == key
                )
                stages.update(
                    {
                        "source_sha256": source["sha256"],
                        "source_bytes": source["bytes"],
                        "acquisition": "complete",
                    }
                )
                self.save("extracting_pois", current_source=key)
                derived = self.root / "derived" / (key + ".pois.jsonl.gz")
                if stages.get("poi_extraction") != "complete" or not derived.exists():
                    self.command(
                        "extract_national_pois", "--district", key, "--root", self.root
                    )
                    stages.update(
                        {
                            "poi_extraction": "complete",
                            "poi_sha256": acquisition.digest_file(derived),
                        }
                    )
                if stages.get("poi_import") != "complete":
                    self.save("importing_pois", current_source=key)
                    self.command(
                        "import_national_inventory",
                        "--district",
                        key,
                        "--root",
                        self.root,
                    )
                    stages["poi_import"] = "complete"
                stages.pop("error", None)
                self.save("source_complete", current_source=key)
            except (
                OSError,
                ValueError,
                RuntimeError,
                subprocess.SubprocessError,
            ) as error:
                stages["error"] = f"{type(error).__name__}: {error}"
                self.save("source_failed", current_source=key, error=stages["error"])
                if "guard" in str(error) or (self.root / "STOP").exists():
                    return
        self.save("poi_pass_complete", current_source=None)
        if self.walking_raw:
            for key, stages in self.state["sources"].items():
                if (
                    stages.get("poi_import") != "complete"
                    or stages.get("walking_raw") == "complete"
                ):
                    continue
                try:
                    self.guard(3 * stages["source_bytes"])
                    self.save("extracting_regional_walking", current_source=key)
                    self.command("extract_regional_walking", "--district", key)
                    stages["walking_raw"] = "complete"
                    stages.pop("walking_error", None)
                    self.save("walking_source_complete", current_source=key)
                except (
                    OSError,
                    ValueError,
                    RuntimeError,
                    subprocess.SubprocessError,
                ) as error:
                    stages["walking_error"] = f"{type(error).__name__}: {error}"
                    self.save(
                        "walking_source_failed",
                        current_source=key,
                        error=stages["walking_error"],
                    )
                    if "guard" in str(error) or (self.root / "STOP").exists():
                        return
        self.save("finished_current_pass", current_source=None)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--env", type=Path, required=True)
    parser.add_argument("--reuse-external-cache", type=Path, required=True)
    parser.add_argument("--minimum-free-gib", type=int, default=15)
    parser.add_argument("--walking-raw", action="store_true")
    args = parser.parse_args()
    for line in args.env.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip().strip("\"'")
    seed_existing(args.repo, args.reuse_external_cache)
    pipeline = NationalPipeline(args.repo, args.minimum_free_gib, args.walking_raw)
    with (pipeline.root / ".pipeline.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        pipeline.run()


if __name__ == "__main__":
    main()
