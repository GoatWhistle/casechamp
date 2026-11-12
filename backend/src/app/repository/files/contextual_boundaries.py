import json
from functools import cached_property
from pathlib import Path

from app.domain.errors import DataUnavailable
from app.usecase.contextual_boundaries import ContextualBoundary


class JsonContextualBoundaryRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    @cached_property
    def records(self) -> list[ContextualBoundary]:
        try:
            rows = json.loads(self.path.read_text())["contextual_regions"]
            result = []
            for row in rows:
                if row.get("display_only") is not True or row.get("analytics_enabled") is not False:
                    raise ValueError("Contextual boundaries must remain display only")
                if not row["id"].startswith("context-"):
                    raise ValueError("Contextual boundary identifiers must be separate")
                result.append(
                    ContextualBoundary(
                        **{
                            **row,
                            "bounds": tuple(row["bounds"]),
                            "polygons": [
                                [
                                    [(float(lon), float(lat)) for lon, lat in ring]
                                    for ring in polygon
                                ]
                                for polygon in row["polygons"]
                            ],
                        }
                    )
                )
            if len({item.id for item in result}) != len(result):
                raise ValueError("Duplicate contextual boundary")
            return result
        except (OSError, ValueError, TypeError, KeyError) as error:
            raise DataUnavailable("Contextual boundary source is unavailable") from error

    def boundaries(self) -> list[ContextualBoundary]:
        return self.records
