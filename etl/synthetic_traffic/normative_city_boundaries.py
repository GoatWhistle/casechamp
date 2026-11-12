import json
import shutil
from pathlib import Path

from analytics.client import ClickHouse
from synthetic_traffic.municipal_boundaries import extract_municipal_boundaries
from synthetic_traffic.municipal_import import import_files

CITIES = [
    ("45000000", "moscow", "central_federal_district"),
    ("40000000", "saint-petersburg", "northwestern_federal_district"),
]


def prepare_city_boundaries(repo):
    repo = Path(repo)
    root = repo / ".local/normative-national-inputs"
    output = root / "municipal-boundaries"
    portable = repo / "datasets/municipal-boundaries/federal-cities"
    output.mkdir(exist_ok=True)
    portable.mkdir(parents=True, exist_ok=True)
    report = []
    for identifier, name, source in CITIES:
        pbf = root / "osm" / (source + ".osm.pbf")
        target = output / (name + ".geojson")
        manifest = target.with_suffix(".manifest.json")
        policy = (
            "source-confirmed-v3" if identifier == "40000000" else "source-confirmed-v2"
        )
        cached = json.loads(manifest.read_text()) if manifest.exists() else {}
        if cached.get("municipal_filter_version") != policy:
            evidence = extract_municipal_boundaries(
                [pbf], root / "regions.json", target, (8,), [identifier], True
            )
            evidence["municipal_filter_version"] = policy
            evidence["municipal_classification_sources"] = [
                "https://www.gov.spb.ru/gov/self_gov/",
                "https://gu.spb.ru/organization/organy-mestnogo-samoupravleniya/66567/",
            ]
            temporary = manifest.with_suffix(".json.part")
            temporary.write_text(json.dumps(evidence, ensure_ascii=False, indent=2))
            temporary.replace(manifest)
        else:
            evidence = cached
        if not evidence["features"]:
            report.append(
                {
                    "region_id": identifier,
                    "status": "municipal_geometry_unavailable",
                    "features": 0,
                }
            )
            continue
        imported = import_files([target])
        for path in [target, manifest]:
            portable_target = portable / path.name
            temporary = portable_target.with_suffix(portable_target.suffix + ".part")
            shutil.copyfile(path, temporary)
            temporary.replace(portable_target)
        report.append(
            {
                "region_id": identifier,
                "status": "partial_source_coverage",
                "features": evidence["features"],
                "inserted": imported["inserted"],
                "source_sha256": evidence["sources"][0]["sha256"],
                "portable_geometry": str((portable / target.name).relative_to(repo)),
            }
        )
    temporary = portable / "import-progress.json.part"
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    temporary.replace(portable / "import-progress.json")
    return report


def municipal_boundary_counts():
    return {
        row["region_id"]: int(row["features"])
        for row in ClickHouse().rows(
            "SELECT region_id,count() AS features FROM plexus_atlas.municipal_boundaries FINAL GROUP BY region_id"
        )
    }
