import json
import re
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.domain.errors import InvalidQuery
from app.usecase.connectivity import ConnectivityResult


def save_result(root: Path, result: ConnectivityResult) -> ConnectivityResult:
    saved = replace(
        result,
        calculation_id="connectivity-" + uuid4().hex,
        calculated_at=datetime.now(UTC).isoformat(),
    )
    folder = root / "connectivity-results"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{saved.calculation_id}.json"
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(asdict(saved), ensure_ascii=False, allow_nan=False))
    temporary.replace(path)
    return saved


def read_result(root: Path, calculation_id: str) -> str:
    if not re.fullmatch(r"connectivity-[a-f0-9]{32}", calculation_id):
        raise InvalidQuery("Invalid connectivity calculation ID")
    path = root / "connectivity-results" / f"{calculation_id}.json"
    if not path.is_file():
        raise InvalidQuery("Saved connectivity calculation was not found")
    return path.read_text()


def recent_results(root: Path) -> str:
    paths = sorted(
        (root / "connectivity-results").glob("connectivity-*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )[:20]
    rows = []
    for path in paths:
        result = json.loads(path.read_text())
        rows.append(
            {
                key: result[key]
                for key in (
                    "calculation_id",
                    "calculated_at",
                    "places",
                    "closed_way_ids",
                    "model_version",
                )
            }
            | {"calculation_type": "connectivity", "status": "done"}
        )
    return json.dumps(rows, ensure_ascii=False)
