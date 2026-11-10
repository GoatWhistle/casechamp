import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import numpy as np
from accessibility.network import best_times, local_matrix
from accessibility.report import assemble, frequencies, regional_values
from accessibility.source import Source
from accessibility.storage import publish
from app.domain.accessibility import MODEL_VERSION


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, choices=range(1, 5), default=2)
    parser.add_argument("--source-revision")
    parser.add_argument("--cache", type=Path, default=Path("data/accessibility-cache"))
    args = parser.parse_args()
    source = Source(args.source_revision)
    if source.metadata["model_version"] != "hansen-release-20261107":
        raise SystemExit(
            "This comparison requires the retained data-20261107 source snapshot"
        )
    code = hashlib.sha256()
    for path in sorted(Path(__file__).parent.glob("*.py")):
        code.update(path.read_bytes())
    code.update(Path("backend/src/app/domain/accessibility.py").read_bytes())
    cache = args.cache / (source.revision[:16] + "-" + code.hexdigest()[:16])
    cache.mkdir(parents=True, exist_ok=True)
    rows = []
    for season in ("summer", "winter"):
        values = {}
        for removed in ("full", "air", "water"):
            checkpoint = cache / f"{season}-{removed}.json"
            if checkpoint.exists():
                saved = json.loads(checkpoint.read_text())
                for mode, records in saved.items():
                    values[mode] = {(r[0], r[1]): tuple(r[2:]) for r in records}
                print(f"Loaded {season} {removed}", flush=True)
                continue
            print(f"Calculating {season} without={removed}", flush=True)
            road, city_roads = local_matrix(source, season, removed, args.workers)
            best = best_times(
                source, road, city_roads, "air" if removed == "air" else None
            )
            values[removed] = regional_values(source, best)
            modes = [removed]
            if removed == "full":
                best = best_times(source, road, city_roads, "rail")
                values["rail"] = regional_values(source, best)
                modes.append("rail")
            saved = {
                mode: [
                    [region, half_life, *v]
                    for (region, half_life), v in values[mode].items()
                ]
                for mode in modes
            }
            checkpoint.write_text(json.dumps(saved, allow_nan=False))
            del road, city_roads, best
        previous_path = cache / f"{season}-previous.json"
        previous = source.previous(season)
        previous.to_json(previous_path, orient="records")
        season_rows = assemble(source, season, values, previous)
        published = source.client.rows(
            "SELECT region_id,hansen FROM plexus_atlas.atlas_indices WHERE scenario='"
            + season
            + "'"
        )
        expected = {r["region_id"]: float(r["hansen"]) for r in published}
        for row in season_rows:
            if row["half_life"] == 2 and not np.isclose(
                row["previous"], expected[row["region_id"]], rtol=1e-6, atol=1e-6
            ):
                raise ValueError("Previous index does not match the published snapshot")
        rows.extend(season_rows)
    if len(rows) != len(source.regions) * 6:
        raise ValueError("Incomplete regional results")
    run = {
        "run_id": uuid4().hex,
        "created_at": datetime.now(UTC).isoformat(),
        "model_version": MODEL_VERSION,
        "source_model": source.metadata["model_version"],
        "source_artifact": source.metadata["artifact_version"],
        "graph_revision": source.metadata["graph_revision"],
        "source_revision": source.revision,
        "normalization": source.normalization,
        "normalization_kind": "legacy_multimodal_road",
        "regions": len(source.regions),
        "markets": len(source.cities),
        "point_count": int(source.points.region.isin(source.regions.region).sum()),
        "frequency_status": "incomplete",
        "assumptions": [
            "planned_departures_no_schedule_wait",
            "terminal_and_access_time_retained",
            "unknown_frequency_not_imputed",
            "ferry_boarding_half_hour",
            "legacy_graph_seasonality_unchanged",
            "half_life_4_8_sensitivity_only",
            "mode_removal_effects_not_additive",
            "new_map_timetables_not_in_calculation",
            "not_gdp_or_passenger_flow",
            "legacy_matrix_72h_cutoff_removed",
        ],
    }
    report = {"run": run, "rows": rows, "frequencies": frequencies(source)}
    (cache / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)
    )
    publish(source, run, rows, report["frequencies"])
    print(json.dumps(run, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
