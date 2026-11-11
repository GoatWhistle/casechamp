from typing import get_type_hints

from analytics.client import ClickHouse
from app.repository.clickhouse.records import sql_type
from app.usecase.road_graph import RoadJob


def main():
    client = ClickHouse()
    hints = get_type_hints(RoadJob)
    for name in ("links", "appraisal_assumptions", "appraisal_result"):
        client.request(
            "ALTER TABLE plexus_state.road_jobs ADD COLUMN IF NOT EXISTS "
            + name + " " + sql_type(hints[name])
        )
    print("Road scenario and appraisal columns are available")


if __name__ == "__main__":
    main()
