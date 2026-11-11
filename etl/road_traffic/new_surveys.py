import hashlib
import json
import re
import subprocess
from pathlib import Path


def survey_record(
    source: str,
    region: str,
    site: str,
    period: str,
    raw: str,
    locator: str,
    quality: str,
    direction: str = "unknown",
) -> dict:
    identity = json.dumps([source, locator, "all", direction], ensure_ascii=False)
    return {
        "observation_id": hashlib.sha256(identity.encode()).hexdigest()[:24],
        "source_id": source,
        "region_id": region,
        "site": site,
        "period": period,
        "unit": "pcu/hour",
        "value": float(raw.replace(",", ".")),
        "raw_value": raw,
        "direction": direction,
        "vehicle_class": "all",
        "source_locator": locator,
        "quality": quality,
    }


def pages_for(pdf: Path, output: Path) -> list[str]:
    text = output / (pdf.stem + ".txt")
    subprocess.run(["pdftotext", "-layout", str(pdf), str(text)], check=True)
    return text.read_text().split("\f")


def obninsk_rows(pages: list[str]) -> list[dict]:
    if "в июне 2025 г." not in pages[110] or "Таблица 1.8.4 -" not in pages[118]:
        raise ValueError("Obninsk source survey context or page layout changed")
    names = {}
    current = None
    for line in pages[111].splitlines():
        match = re.match(r"^\s*(\d{1,2})\s+(.+)$", line)
        if match and 1 <= int(match[1]) <= 22:
            current = int(match[1])
            names[current] = match[2].strip()
        elif current and line.strip() and not line.strip().isdigit():
            names[current] += " " + line.strip()
    expression = re.compile(
        r"^\s*(\d{1,2})\s+(.*?)\s*(\d+(?:,\d+)?)\s+"
        r"(\d+(?:,\d+)?)\s+(\d+(?:,\d+)?)\s+(\d+(?:,\d+)?)\s*$"
    )
    rows = []
    seen = []
    for line in pages[118].splitlines():
        match = expression.match(line)
        if not match:
            continue
        site = int(match[1])
        seen.append(site)
        roads = [
            re.sub(r"^(?:Пересечение|Пресечение)\s+", "", part.strip())
            for part in re.split(r"\s+-\s+|\s+с\s+|\s+и\s+", names[site])
        ]
        for index, period in enumerate(
            ["morning_peak", "interpeak", "evening_peak"], 3
        ):
            row = survey_record(
                "traffic-obninsk",
                "29000000",
                names[site],
                "2025-06; " + period + "; exact dates and clock times unspecified",
                match[index],
                f"PDF page 119; table 1.8.4; site {site}; {period}",
                "reported_video_survey; junction aggregate; direction unresolved; visually checked",
            )
            row.update(
                site_id=str(site),
                city="Обнинск",
                road_name=roads[0],
                candidate_road_names=roads,
                metric=period,
                measurement_extent="junction_aggregate",
                assignment_policy="do_not_assign_junction_total_to_individual_roads",
                reported_derived_parameters={
                    "reported_daily_interinterval_intensity": match[6],
                    "source_column": "Среднесуточная межинтервальная интенсивность",
                    "status": "reported aggregate; not an independent observation",
                },
            )
            rows.append(row)
    if seen != list(range(1, 23)) or len(names) != 22:
        raise ValueError("Expected exactly 22 Obninsk junction rows")
    return rows


def birobidzhan_rows(pages: list[str]) -> list[dict]:
    if "Таблица 5 –" not in pages[77] or "Таблица 6 –" not in pages[78]:
        raise ValueError("Birobidzhan source page layout changed")
    sites = {}
    current = None
    for line in pages[77].splitlines():
        coordinate = re.match(r"^\s*(\d{1,2})\s+(\d{2}\.\d+),\s*(\d{3}\.\d+)\s*$", line)
        if coordinate:
            current = int(coordinate[1])
            sites[current] = {"lat": float(coordinate[2]), "lon": float(coordinate[3])}
        elif current and "Россия, ул." in line:
            sites[current]["road_name"] = line.split("Россия, ", 1)[1].strip()
    rows = []
    seen = []
    for page in [79, 80]:
        for line in pages[page - 1].splitlines():
            match = re.match(r"^\s*(\d{1,2})\s+(\d+)\s*$", line)
            if not match:
                continue
            site = int(match[1])
            seen.append(site)
            details = sites[site]
            row = survey_record(
                "traffic-birobidzhan",
                "99000000",
                "Биробиджан; " + details["road_name"],
                "observation date unspecified; document planning horizon 2020-2030",
                match[2],
                f"PDF page {page}; table 6; site {site}; coordinates PDF page 78 table 5",
                "reported_survey_maximum; observation date unresolved; visually checked",
                direction="one direction in source definition; compass and OSM orientation unspecified",
            )
            row.update(
                details,
                site_id=str(site),
                city="Биробиджан",
                metric="reported_maximum_hour",
                measurement_extent="road_section_counter",
                coordinate_source="PDF page 78; table 5",
            )
            rows.append(row)
    if seen != list(range(1, 11)) or len(sites) != 10:
        raise ValueError("Expected exactly 10 Birobidzhan sites")
    return rows


def additional_observations(root: Path, output: Path) -> list[dict]:
    output.mkdir(parents=True, exist_ok=True)
    raw = root / "data/additional/road-traffic/raw"
    rows = []
    sources = []
    for name, extractor in [
        ("obninsk-ksodd-2025", obninsk_rows),
        ("birobidzhan-ksodd", birobidzhan_rows),
    ]:
        pdf = raw / (name + ".pdf")
        extracted = extractor(pages_for(pdf, output))
        digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
        for row in extracted:
            row["source_sha256"] = digest
        rows.extend(extracted)
        sources.append(
            {"file": pdf.name, "sha256": digest, "observations": len(extracted)}
        )
    if len({row["observation_id"] for row in rows}) != len(rows):
        raise ValueError("Duplicate new survey observation identity")
    (output / "new-survey-observations.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2)
    )
    (output / "new-survey-extraction.json").write_text(
        json.dumps(sources, ensure_ascii=False, indent=2)
    )
    return rows
