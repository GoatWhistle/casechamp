import hashlib
import html
import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

ALIASES = {
    "Ненецкий АО": "Ненецкий автономный округ",
    "ЯНАО": "Ямало-Ненецкий автономный округ",
    "Чукотский АО": "Чукотский автономный округ",
    "Республика Саха (Якутия)": "Республика Саха",
    "Республика Северная Осетия": "Республика Северная Осетия - Алания",
    "Ханты-Мансийский автономный округ": "Ханты-Мансийский автономный округ - Югра",
}
DIRECTORY_URL = "https://www.mintrans.gov.ru/activities"


def normalized(value: str) -> str:
    return " ".join(value.split())


def owners_for_regions(root: Path, registry: Path) -> list[dict]:
    regions = json.loads(
        (root / "datasets/additional/all-regions/atlas-regions.json").read_text()
    )
    owners = json.loads((registry / "official-owners.json").read_text())
    by_name = {normalized(row["title"]): row for row in owners}
    searches = {
        row["name"]: row
        for row in json.loads((registry / "search-results.json").read_text())
    }
    result = []
    for region in regions:
        row = by_name[ALIASES.get(region["name"], region["name"])]
        url = row["site"]
        if not url.startswith("http"):
            url = "https://" + url
        result.append(
            {
                "region_id": region["region_id"],
                "region_name": region["name"],
                "owner_name": row["podrazdelenie"],
                "owner_url": url,
                "owner_provenance": DIRECTORY_URL,
                "traffic_search_query": searches[region["name"]]["query"],
                "search_status": searches[region["name"]]["status"],
                "search_evidence": "search-results.json",
                "dataset_status": "no_segment_measurements_verified_from_search",
            }
        )
    official = registry / "official-site-searches.json"
    if official.exists():
        indexed = {row["region_id"]: row for row in json.loads(official.read_text())}
        for row in result:
            evidence = indexed[row["region_id"]]
            row["official_site_query"] = evidence.get("query", "")
            row["official_site_search_status"] = evidence["status"]
            row["official_site_search_evidence"] = "official-site-searches.json"
    return result


def inspect_owner(record: dict, output: Path) -> dict:
    row = dict(record)
    row["checked_at"] = datetime.now(UTC).isoformat()
    url = row["owner_url"]
    suffix = hashlib.sha256(url.encode()).hexdigest()[:8]
    target = output / (row["region_id"] + "-" + suffix + "-owner.html")
    try:
        request = Request(
            url, headers={"User-Agent": "Plexus public road data research"}
        )
        with urlopen(request, timeout=8) as response:
            content = response.read(2_000_001)
            row["http_status"] = response.status
            row["final_url"] = response.url
        if len(content) > 2_000_000:
            row["content_truncated"] = True
            content = content[:2_000_000]
        target.write_bytes(content)
        row.update(
            owner_check_status="page_retrieved",
            owner_page=str(target),
            owner_page_sha256=hashlib.sha256(content).hexdigest(),
        )
        text = content.decode("utf-8", errors="replace")
        if "windows-1251" in text[:5000].lower():
            text = content.decode("cp1251", errors="replace")
        links = []
        for match in re.finditer(
            r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
            text,
            re.IGNORECASE | re.DOTALL,
        ):
            label = normalized(html.unescape(re.sub("<[^>]+>", " ", match[2])))
            if re.search(
                "интенсив|уч[её]т.*движ|открыт.*дан|ксодд|traffic|opendata",
                label + match[1],
                re.IGNORECASE,
            ):
                links.append(
                    {
                        "url": urljoin(row["final_url"], html.unescape(match[1])),
                        "title": label,
                    }
                )
        row["relevant_navigation"] = links
        row["data_access_status"] = (
            "navigation_found" if links else "no_relevant_navigation_on_owner_homepage"
        )
    except (OSError, ValueError) as error:
        row.update(owner_check_status="page_unavailable", error=str(error))
    return row


def inspect_regions(root: Path, registry: Path, output: Path) -> list[dict]:
    output.mkdir(parents=True, exist_ok=True)
    regions = owners_for_regions(root, registry)
    with ThreadPoolExecutor(max_workers=8) as executor:
        rows = list(executor.map(lambda row: inspect_owner(row, output), regions))
    (registry / "regional-source-checks.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2)
    )
    return rows
