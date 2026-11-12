import argparse
import hashlib
import json
import re
import zipfile
from dataclasses import asdict
from pathlib import Path
from xml.etree import ElementTree

from analytics.client import ClickHouse
from app.domain.normative.territory import ENCODED_PARENT_STATUS, TerritoryContext

REFERENCE_URL = "https://www.nalog.gov.ru/rn45/news/activities_fts/14849279/"
FILE_URL = "https://www.nalog.gov.ru/html/sites/www.rn45.nalog.ru/OKTMO.docx"
STRUCTURE_URL = "https://www.nalog.gov.ru/rn27/news/activities_fts/6061590/"
EXPECTED_SHA256 = "03051ab2fcd571969461311e39b151783c3c783457f0f0862de784f82abddd13"


def reference_codes(path: Path) -> list[dict]:
    if hashlib.sha256(path.read_bytes()).hexdigest() != EXPECTED_SHA256:
        raise ValueError("The 2024 municipal reference checksum does not match")
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    result = []
    for row in root.findall(".//w:tr", ns):
        cells = [
            " ".join(" ".join(t.text or "" for t in cell.findall(".//w:t", ns)).split())
            for cell in row.findall("w:tc", ns)
        ]
        if len(cells) != 2 or re.fullmatch(r"37[57][0-9]{5}", cells[0]) is None:
            continue
        kind = "municipal_okrug" if "муниципальный округ" in cells[1] else "urban_okrug"
        if kind == "urban_okrug" and not cells[1].startswith("г."):
            raise ValueError("Unknown municipality category in the 2024 source")
        result.append({"code": cells[0], "name": cells[1], "municipality_type": kind})
    if len(result) != 26 or len({r["code"] for r in result}) != 26:
        raise ValueError("Expected exactly 26 distinct 2024 municipality codes")
    if sum(r["municipality_type"] == "municipal_okrug" for r in result) != 24:
        raise ValueError("Unexpected municipal reference composition")
    return result


def encoded_contexts(
    point_ids: list[str], reference: list[dict], overrides: list[dict]
) -> list[dict]:
    if len(set(point_ids)) != len(point_ids):
        raise ValueError("Duplicate origin identifiers")
    existing = {r["point_id"]: r for r in overrides}
    if len(existing) != len(overrides):
        raise ValueError("Duplicate manual territorial evidence")
    codes = {r["code"]: r for r in reference}
    if len(codes) != len(reference):
        raise ValueError("Duplicate municipality codes")
    result = list(overrides)
    for point_id in sorted(point_ids):
        if point_id in existing or re.fullmatch(r"[0-9]{11}", point_id) is None:
            continue
        parent = codes.get(point_id[:8])
        if parent is None:
            continue
        context = TerritoryContext(
            point_id,
            parent["municipality_type"],
            REFERENCE_URL,
            ENCODED_PARENT_STATUS,
            parent["code"],
            STRUCTURE_URL,
        )
        result.append(asdict(context))
    return sorted(result, key=lambda r: r["point_id"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input", type=Path, default=Path(".local/municipal-crosswalk/OKTMO-full-2024.docx")
    )
    parser.add_argument("--output", type=Path, default=Path("datasets/normative-territories.json"))
    args = parser.parse_args()
    reference = reference_codes(args.input)
    previous = json.loads(args.output.read_text())
    overrides = [
        r for r in previous["territories"] if r["verification_status"] != ENCODED_PARENT_STATUS
    ]
    points = ClickHouse().rows(
        "SELECT point_id FROM plexus_graph.locations "
        "WHERE region='Курганская область' ORDER BY point_id"
    )
    contexts = encoded_contexts([r["point_id"] for r in points], reference, overrides)
    provenance = {
        "source_url": REFERENCE_URL,
        "file_url": FILE_URL,
        "sha256": EXPECTED_SHA256,
        "reference_date": "2024-01-01",
        "structure_source_url": STRUCTURE_URL,
        "structure_source_date": "2016-05-04",
        "assignment_verified": False,
        "currentness_verified": False,
        "municipalities": reference,
    }
    Path("datasets/normative-municipal-code-reference.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n"
    )
    args.output.write_text(
        json.dumps(
            {"observed_at": "2026-11-12", "territories": contexts}, ensure_ascii=False, indent=2
        )
        + "\n"
    )
    print("territorial contexts", len(contexts), "encoded", len(contexts) - len(overrides))


if __name__ == "__main__":
    main()
