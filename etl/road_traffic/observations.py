import csv
import hashlib
import json
import math
import re
from pathlib import Path

from road_traffic.new_surveys import additional_observations
from road_traffic.sources import acquire_sources, xlsx_rows


def number(value: str) -> float | None:
    if not value or value.strip() in {"-", "—"}:
        return None
    try:
        parsed = float(value.strip().replace(",", "."))
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) and parsed >= 0 else None


def observation(
    source: str,
    region: str,
    site: str,
    period: str,
    unit: str,
    raw: str,
    locator: str,
    quality: str,
    vehicle: str = "all",
    direction: str = "unknown",
) -> dict:
    identity = json.dumps([source, locator, vehicle, direction], ensure_ascii=False)
    return {
        "observation_id": hashlib.sha256(identity.encode()).hexdigest()[:24],
        "source_id": source,
        "region_id": region,
        "site": site,
        "period": period,
        "unit": unit,
        "value": number(raw),
        "raw_value": raw,
        "direction": direction,
        "vehicle_class": vehicle,
        "source_locator": locator,
        "quality": quality,
    }


def survey_observations(root: Path) -> list[dict]:
    base = root / "data/additional/traffic-surveys"
    result = []
    for town, region, period in [
        ("serov", "65000000", "2018-09-17/2018-09-20"),
        ("nefteyugansk", "71800000", "2018-10-30"),
    ]:
        path = base / f"{town}-observed-parameters.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing existing survey: {path}")
        with path.open() as stream:
            for index, row in enumerate(csv.DictReader(stream), 1):
                item = observation(
                    "traffic-" + town,
                    region,
                    row.get("location", row.get("street", "")),
                    period,
                    "pcu/hour",
                    row["intensity_pcu_per_hour"],
                    f"PDF page {row['pdf_page']}; table {row['table']}; row {index}",
                    "reported_observation; historical; no coordinates; direction unresolved",
                )
                item["reported_derived_parameters"] = {
                    key: value
                    for key, value in row.items()
                    if key
                    in {
                        "capacity_pcu_per_hour",
                        "speed_kmh",
                        "density_vehicles_per_km",
                        "density_reported_pcu",
                        "load_ratio",
                    }
                }
                item["road_name"] = item["site"].split(" (от ")[0].split(" / ")[0]
                item["candidate_road_names"] = [
                    name.strip() for name in item["site"].split(" / ")
                ]
                result.append(item)
    path = base / "belovo-observed-vehicle-counts.csv"
    with path.open() as stream:
        for row in csv.DictReader(stream):
            locator = (
                f"PDF page {row['pdf_page']}; table {row['table']}; "
                f"site {row['site_sequence']}; column {row['column_index']}"
            )
            result.append(
                observation(
                    "traffic-belovo",
                    "32000000",
                    "survey site " + row["site_sequence"],
                    "document 2019; date unresolved; " + row["peak_period"],
                    "vehicles/reported survey interval",
                    row["count_raw"],
                    locator,
                    "reported_observation; interval duration and direction unresolved; missing retained",
                    row["vehicle_type"],
                    "original column " + row["column_index"],
                )
            )
    return result


def kuzbass_observations(path: Path) -> list[dict]:
    rows = xlsx_rows(path)
    title = next(row.get("A", "") for row in rows if row["row"] == "2")
    classes = next(row for row in rows if row["row"] == "6")
    result = []
    road = ""
    for row in rows:
        if int(row["row"]) < 8:
            continue
        if number(row.get("S", "")) is None:
            if row.get("A") and number(row["A"]) is None:
                road = row["A"]
            continue
        site = road + "; km " + row.get("A", "")
        direction = (
            "reported reverse corridor direction"
            if "обратное направление" in road
            else "reported forward corridor direction"
            if "прямое направление" in road
            else "unknown"
        )
        class_values = [number(row.get(column, "")) for column in "EFGHIJKLMNOPQR"]
        complete = all(value is not None for value in class_values)
        difference = sum(value or 0 for value in class_values) - float(row["S"])
        quality = (
            "reported_observation; observation year unresolved; directions unspecified"
        )
        if complete and abs(difference) > 0.001:
            quality += "; published class sum differs from total"
        for column in "EFGHIJKLMNOPQRST":
            unit = "pcu/day" if column == "T" else "vehicles/day"
            item = observation(
                "traffic-kuzbass",
                "32000000",
                site,
                title,
                unit,
                row.get(column, ""),
                f"Опорная сеть!{column}{row['row']}",
                quality,
                classes.get(column, "all"),
                direction,
            )
            item.update(
                road=road,
                road_name=re.sub(r"\s*\((?:прямое|обратное) направление\)", "", road),
                counter_km_raw=row.get("A", ""),
                counter_km=number(row.get("A", "")),
                section_start_km=number(row.get("B", "")),
                section_end_km=number(row.get("C", "")),
                class_sum_difference=difference if complete else None,
            )
            result.append(item)
        for column, metric in [
            ("U", "maximum_hour"),
            ("V", "maximum_hour_pcu"),
            ("W", "50th_hour"),
            ("X", "maximum_day"),
        ]:
            item = observation(
                "traffic-kuzbass",
                "32000000",
                site,
                title,
                "vehicles/day"
                if column == "X"
                else ("pcu/hour" if column == "V" else "vehicles/hour"),
                row.get(column, ""),
                f"Опорная сеть!{column}{row['row']}",
                "reported_extreme; derivation method unverified; "
                + (
                    "spreadsheet formula"
                    if row.get(column + "_formula")
                    else "cached source value"
                ),
            )
            item.update(metric=metric, road=road)
            result.append(item)
    return result


def collect_observations(root: Path, output: Path) -> tuple[list[dict], list[dict]]:
    output.mkdir(parents=True, exist_ok=True)
    sources = acquire_sources(root, output)
    result = survey_observations(root)
    kuzbass = next(
        source for source in sources if source["source_id"] == "traffic-kuzbass"
    )
    if kuzbass["status"] == "downloaded":
        result.extend(kuzbass_observations(Path(kuzbass["path"])))
    result.extend(additional_observations(root, output))
    for source in sources:
        source["observation_count"] = sum(
            row["source_id"] == source["source_id"] for row in result
        )
        source["normalization_status"] = (
            "normalized_reported_observations"
            if source["observation_count"]
            else "document_saved_not_normalized"
        )
        if source["source_id"] == "traffic-ugra":
            source["normalization_status"] = (
                "OCR requires visual verification; no numeric observations imported"
            )
    if len({row["observation_id"] for row in result}) != len(result):
        raise ValueError("Duplicate observation identity")
    (output / "observations.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2)
    )
    (output / "sources.json").write_text(
        json.dumps(sources, ensure_ascii=False, indent=2)
    )
    return result, sources
