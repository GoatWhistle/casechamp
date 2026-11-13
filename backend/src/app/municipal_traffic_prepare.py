import argparse
import os
from pathlib import Path

from app.adapter.road_graph.data import GraphData
from app.adapter.traffic.municipal_baselines import MunicipalBaselines
from app.adapter.traffic.municipal_connectivity import MunicipalConnectivity
from app.repository.clickhouse.atlas import ClickHouseAtlasRepository
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot
from app.repository.clickhouse.municipal_indices import ClickHouseMunicipalIndexRepository
from app.repository.clickhouse.municipalities import ClickHouseMunicipalRepository
from app.settings import load_settings
from app.usecase.municipalities import MunicipalityQueries


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--graph", type=Path, required=True)
    args = parser.parse_args()
    config = load_settings(os.environ)
    reader = ClickHouseReader(config.clickhouse_url, config.clickhouse_user, config.clickhouse_password)
    atlas = ClickHouseAtlasRepository(reader)
    municipalities = MunicipalityQueries(ClickHouseMunicipalRepository(reader), atlas)
    baselines = MunicipalBaselines(args.graph.parent / "municipal-traffic-baselines", municipalities)
    effects = MunicipalConnectivity(GraphData(args.graph, ClickHouseGraphSnapshot(reader)), baselines,
                                    ClickHouseMunicipalIndexRepository(reader))
    print(effects.prepare(args.baseline, args.region, lambda: None), flush=True)


if __name__ == "__main__":
    main()
