import json
from functools import cached_property
from pathlib import Path

from app.domain.errors import DataUnavailable
from app.usecase.contextual_water import ContextualWater


class JsonContextualWaterRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    @cached_property
    def records(self) -> list[ContextualWater]:
        try:
            rows = json.loads(self.path.read_text())["contextual_water"]
            result = []
            for row in rows:
                if row.get("display_only") is not True or row.get("analytics_enabled") is not False:
                    raise ValueError("Contextual water must remain display only")
                result.append(
                    ContextualWater(
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
            return result
        except (OSError, ValueError, TypeError, KeyError) as error:
            raise DataUnavailable("Contextual water source is unavailable") from error

    def boundaries(self) -> list[ContextualWater]:
        return self.records
