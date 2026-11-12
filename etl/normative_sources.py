import argparse
import hashlib
import json
import re
import subprocess
import time
from datetime import UTC, datetime
from html import unescape
from pathlib import Path
from urllib.parse import urlencode

from normative_address import address_matches

URL = "https://www.mfc45.ru/mfc-map.html"
GEOCODER = "https://nominatim.openstreetmap.org/search"


def download(url: str) -> bytes:
    return subprocess.check_output(
        [
            "curl",
            "-fsSL",
            "--max-time",
            "30",
            "-A",
            "PlexusTransportResearch/1.0 https://github.com/GoatWhistle/casechamp",
            url,
        ]
    )


def text(value: str) -> str:
    return " ".join(unescape(re.sub("<[^>]+>", " ", value)).split())


def departments(html: str) -> list[dict[str, object]]:
    entries = []
    pattern = r'id="department-info-block-(\d+)"[\s\S]*?<h3[^>]*>([\s\S]*?)</h3>\s*<p>([\s\S]*?)</p>'
    for key, title, address in re.findall(pattern, html):
        clean = re.split(r"тел[.:]", text(address), maxsplit=1)[0].rstrip(" ,")
        entries.append(
            {
                "id": "mfc-" + key,
                "service": "mfc",
                "name": text(title),
                "address": clean,
                "source_url": URL,
            }
        )
    if len(entries) < 20 or len({item["id"] for item in entries}) != len(entries):
        raise ValueError("Unexpected official facility directory structure")
    return entries


def geocode(
    address: str, folder: Path
) -> tuple[float | None, float | None, str | None]:
    query = re.sub(r"^(?:м\.о\.|г\.о\.)[^,]+,", "", address)
    query = re.split(r",?\s*(?:помещ|этаж|ТРЦ)", query)[0]
    query = re.sub(r"\b(?:ул\.|зд\.|здание|стр\.|д\.|город|помещение)\s*", " ", query)
    query = re.sub(r"(?<!\w)(?:г\.|с\.|рп|р\.п\.)\s*", " ", query)
    query = re.sub(r"[,;]", " ", query)
    params = {
        "q": "Курганская область, " + query,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": 1,
        "countrycodes": "ru",
    }
    url = GEOCODER + "?" + urlencode(params)
    cache = folder / (hashlib.sha256(url.encode()).hexdigest() + ".json")
    if not cache.exists():
        time.sleep(1.1)
        try:
            cache.write_bytes(download(url))
        except subprocess.CalledProcessError:
            return None, None, None
    values = json.loads(cache.read_bytes())
    if values:
        row = values[0]
        lat, lon = float(row["lat"]), float(row["lon"])
        if (
            row.get("place_rank", 0) >= 30
            and 54 < lat < 57 and 61 < lon < 69
            and address_matches(address, row.get("address", {}))
        ):
            return lat, lon, url
    return None, None, None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=Path("datasets/normative/mfc.json")
    )
    parser.add_argument("--geocode", action="store_true")
    args = parser.parse_args()
    folder = Path(".local/normative-sources")
    folder.mkdir(parents=True, exist_ok=True)
    raw = download(URL)
    (folder / "mfc-map.html").write_bytes(raw)
    observed = datetime.now(UTC).isoformat()
    facilities = departments(raw.decode("utf-8"))
    for entry in facilities:
        lat, lon, source = (
            geocode(str(entry["address"]), folder)
            if args.geocode
            else (None, None, None)
        )
        entry.update(
            observed_at=observed,
            source_sha256=hashlib.sha256(raw).hexdigest(),
            latitude=lat,
            longitude=lon,
            coordinate_source=source,
            coordinate_status="geocoded_building" if source else "missing",
        )
        print(entry["id"], entry["coordinate_status"], flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {
                "source_url": URL,
                "observed_at": observed,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "coordinate_licence": "ODbL-1.0",
                "facilities": facilities,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
