import json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from app.domain.errors import DataUnavailable
from app.usecase.normative.index_map_models import IndexMapRegion
from app.usecase.normative.route import RouteStage

REPORT_LABEL = "docs/results/normative-live-index-coverage.json"


class ArchivedIndexMapRepository:
    def __init__(self, report_path: Path) -> None:
        self.report_path = report_path
        self._archive: dict[str, list[IndexMapRegion]] | None = None

    def regions(self, criterion_id: str, stage: RouteStage) -> list[IndexMapRegion]:
        if stage != "scenario":
            raise DataUnavailable("The archived report has scenario aggregates only")
        if self._archive is None:
            self._archive = self._load()
        return list(self._archive.get(criterion_id, []))

    def _load(self) -> dict[str, list[IndexMapRegion]]:
        try:
            raw = self.report_path.read_bytes()
            report = json.loads(raw)
            checked_at = report["checked_at"]
            if not isinstance(checked_at, str) or report["legal_compliance_confirmed"] is not False:
                raise ValueError("Archived aggregate provenance is incomplete")
            result = {}
            digest = sha256(raw).hexdigest()
            for group in report["results"]:
                criterion = str(group["criterion_id"])
                if criterion in result:
                    raise ValueError("Duplicate archived criterion")
                rows = [IndexMapRegion(**row) for row in group["rows"]]
                if len({row.region_id for row in rows}) != len(rows) or any(
                    row.legal_compliance_confirmed for row in rows
                ):
                    raise ValueError("Archived aggregate regions or qualification are invalid")
                result[criterion] = [
                    replace(
                        row,
                        data_source="archived_aggregate",
                        source_report=REPORT_LABEL,
                        source_report_sha256=digest,
                        source_checked_at=checked_at,
                        detail_available=False,
                    )
                    for row in rows
                ]
            return result
        except (OSError, ValueError, TypeError, KeyError) as error:
            raise DataUnavailable("Archived normative aggregates are unavailable") from error
