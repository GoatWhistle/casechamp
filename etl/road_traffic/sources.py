import hashlib
import json
import shutil
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen
from xml.etree import ElementTree

KNOWN = [
    (
        "traffic-kuzbass",
        "32000000",
        "kuzbass-2026.xlsx",
        "https://kuzdor.ru/wp-content/KuzdorSiteSection/OurActivity/RoadMaintenance/IntensityReport/Intensivnost-01.01.2026.xlsx",
        "",
        "2023 in title; snapshot 2026-01-01; observation year unresolved",
    ),
    (
        "traffic-serov",
        "65000000",
        "serov-ksodd.pdf",
        "https://www.adm-serov.ru/files/statica/KJKH/KSODD1.pdf?schema=white",
        "traffic-surveys/raw/serov-ksodd.pdf",
        "2018-09-17/2018-09-20",
    ),
    (
        "traffic-nefteyugansk",
        "71800000",
        "nefteyugansk-ksodd.pdf",
        "https://www.admugansk.ru/uploads/2018/11/3ksodd.pdf",
        "traffic-surveys/raw/nefteyugansk-ksodd.pdf",
        "2018-10-30",
    ),
    (
        "traffic-belovo",
        "32000000",
        "belovo-ksodd.pdf",
        "https://www.belovorn.ru/LOAD_CONTENT/Район/Дорожное хозяйство/КСОДД Беловского муниципального района.pdf",
        "traffic-surveys/raw/belovo-ksodd.pdf",
        "document 2019; observation dates unresolved",
    ),
    (
        "traffic-ugra",
        "71800000",
        "ugra-2022.pdf",
        "https://www.ugrador.ru/upload/medialibrary/3f8/928499uaw013etis7tr96pj8bftswrbr/Intensivnost-na-dorogakh-KHMAO-za-2022-g..pdf",
        "road-assets-ugra/raw/Intensivnost-na-dorogakh-KHMAO-za-2022-g..pdf",
        "2022",
    ),
    (
        "traffic-obninsk",
        "29000000",
        "obninsk-ksodd-2025.pdf",
        "https://www.admobninsk.ru/netcat_files/File/ksodd-2025-go-obninsk-kaluzhskoi-oblasti-21-11-2025.pdf",
        "",
        "document 2025-11-21; observation dates unverified",
    ),
    (
        "traffic-birobidzhan",
        "99000000",
        "birobidzhan-ksodd.pdf",
        "https://www.biradm.ru/files/jkh/%D0%9A%D0%A1%D0%9E%D0%94%D0%94%20%D0%9C%D0%9E%20%D0%B3.%20%D0%91%D0%B8%D1%80%D0%BE%D0%B1%D0%B8%D0%B4%D0%B6%D0%B0%D0%BD.pdf",
        "",
        "document and observation dates unverified",
    ),
    (
        "traffic-temryuk",
        "03000000",
        "temryuk-ksodd-2019.pdf",
        "https://www.temryuk.ru/nash-rayon/transport-svyaz-i-dor-khoz/files/shema-dd-motr-2019-2-2.pdf",
        "",
        "document 2019; observation dates unverified",
    ),
]


def acquire_sources(root: Path, output: Path) -> list[dict]:
    raw = output / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    records = []
    for source_id, region, filename, url, existing, period in KNOWN:
        target = raw / filename
        record = {
            "source_id": source_id,
            "region_id": region,
            "url": url,
            "period": period,
            "license": "not established; attribution retained",
            "checked_at": datetime.now(UTC).isoformat(),
        }
        try:
            previous = root / "data/additional" / existing if existing else None
            if not target.exists() and previous and previous.is_file():
                shutil.copyfile(previous, target)
                record["retrieval_method"] = "existing_project_snapshot"
            elif not target.exists():
                request = Request(
                    url, headers={"User-Agent": "Plexus research data collector"}
                )
                with urlopen(request, timeout=25) as response:
                    payload = response.read()
                expected = b"PK" if target.suffix == ".xlsx" else b"%PDF"
                if not payload.startswith(expected):
                    raise ValueError("Unexpected content signature")
                temporary = target.with_suffix(target.suffix + ".part")
                temporary.write_bytes(payload)
                temporary.replace(target)
                record["retrieval_method"] = "https_download"
            else:
                record["retrieval_method"] = "cached_local_snapshot"
            record.update(
                status="downloaded",
                path=str(target),
                bytes=target.stat().st_size,
                sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                retrieved_at=datetime.fromtimestamp(
                    target.stat().st_mtime, UTC
                ).isoformat(),
            )
        except (OSError, ValueError) as error:
            record.update(status="download_failed", error=str(error))
        records.append(record)
    (output / "sources.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2)
    )
    return records


def xlsx_rows(path: Path) -> list[dict[str, str]]:
    namespace = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as archive:
        strings = [
            "".join(node.itertext())
            for node in ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
        ]
        document = ElementTree.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        result = []
        for row in document.findall(".//s:row", namespace):
            cells = {"row": row.attrib["r"]}
            for cell in row:
                value = cell.find("s:v", namespace)
                if value is not None:
                    text = value.text or ""
                    cells[cell.attrib["r"].rstrip("0123456789")] = (
                        strings[int(text)] if cell.attrib.get("t") == "s" else text
                    )
                    if cell.find("s:f", namespace) is not None:
                        cells[cell.attrib["r"].rstrip("0123456789") + "_formula"] = (
                            "true"
                        )
            result.append(cells)
        return result
