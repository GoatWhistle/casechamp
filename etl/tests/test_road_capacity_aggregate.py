import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pyarrow as pa

ROOT = Path(__file__).resolve().parents[2]
MAIN = Path(os.environ.get("ROAD_CAPACITY_SOURCE_ROOT", ROOT))
sys.path[:0] = [str(ROOT / "etl"), str(MAIN / "etl"), str(MAIN / "backend/src")]

from road_capacity.aggregate import rebuild_indices
from road_capacity.storage import CapacityStore


@unittest.skipUnless(
    os.environ.get("ROAD_CAPACITY_INTEGRATION") == "1",
    "Explicit scratch ClickHouse integration run",
)
class AggregateIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        url = os.environ.get("TRAFFIC_TEST_CLICKHOUSE_URL")
        if not url:
            raise RuntimeError("TRAFFIC_TEST_CLICKHOUSE_URL is required")
        cls.environment = patch.dict(
            os.environ,
            {
                "CLICKHOUSE_URL": url,
                "CLICKHOUSE_USER": os.environ.get(
                    "TRAFFIC_TEST_CLICKHOUSE_USER", "default"
                ),
                "CLICKHOUSE_PASSWORD": os.environ.get(
                    "TRAFFIC_TEST_CLICKHOUSE_PASSWORD", ""
                ),
            },
        )
        cls.environment.start()
        cls.store = CapacityStore()
        cls.database = "plexus_capacity_test_" + uuid4().hex
        cls.store.execute(f"CREATE DATABASE {cls.database}")
        schema = (
            (MAIN / "infra/clickhouse/snapshot-schema.sql").read_text().splitlines()
        )
        for name in ["idx_np", "idx_mo", "idx_region", "idx_theil", "idx_np_gap"]:
            line = next(
                line
                for line in schema
                if line.startswith("CREATE TABLE plexus_casechamp." + name + " (")
            )
            cls.store.execute(
                line.replace("plexus_casechamp." + name, cls.database + "." + name)
            )
        cls.store.execute(
            f"CREATE TABLE {cls.database}.reference_idx_region AS {cls.database}.idx_region"
        )
        cls.store.execute(
            f"INSERT INTO {cls.database}.reference_idx_region (region) SELECT concat('r',toString(number)) FROM numbers(82)"
        )

    @classmethod
    def tearDownClass(cls):
        try:
            cls.store.execute(f"DROP DATABASE {cls.database} SYNC")
        finally:
            cls.environment.stop()

    def test_82_region_aggregates_inequality_and_seasonal_gaps(self):
        store, database = self.store, self.database
        fields = [
            row["name"] for row in store.rows(f"DESCRIBE TABLE {database}.idx_np")
        ]
        rows = []
        for region in range(82):
            for season in ["road", "summer", "winter"]:
                for index in [0, 1]:
                    row = dict.fromkeys(fields)
                    value = 1000.0 if index == 0 else 3000.0
                    row.update(
                        season=season,
                        point_id=f"r{region}p{index}",
                        name=f"Point {index}",
                        region=f"r{region}",
                        mun_upper="m",
                        population=100 if index == 0 else 300,
                        is_rural=True,
                        is_dc=index == 1,
                        on_road=True,
                        manual_only=False,
                        no_all_season_road=False,
                        hansen_1h=value / 2,
                        hansen_2h=value,
                        hansen_4h=value * 2,
                        hansen_idx=value / 100,
                        harris=value,
                        remoteness_ca=0.2 if index == 0 else 0.8,
                        cum_pop_1h=value,
                        cum_pop_2h=value,
                        cum_pop_4h=value,
                        t_city50k_road_h=0.5 if index == 0 else 1.5,
                        t_city50k_best_h=0.5 if index == 0 else 1.5,
                        oecd_remote=index == 1,
                        t_aria_a=1.0,
                        t_aria_b=1.0,
                        t_aria_c=1.0,
                        t_aria_d=1.0,
                        t_aria_e=1.0,
                        aria=1.0 if index == 0 else 10.0,
                        aria_class="major_city" if index == 0 else "remote",
                        t_district_center_h=0.5,
                        lancet_2h=True,
                        km_allseason_road=1.0 if index == 0 else 3.0,
                        rai_2km=index == 0,
                        net_efficiency=1.0 if index == 0 else 2.0,
                        t_capital_best_h=1.0,
                    )
                    rows.append(row)
        store.insert_arrow(database + ".idx_np", pa.Table.from_pylist(rows))
        with patch("road_capacity.aggregate.CASE", database):
            rebuilt = rebuild_indices(store, {"poverty_cutoff": 1500.0})
        self.assertEqual(len(rebuilt), 3)
        result = store.rows(
            f"SELECT * FROM {database}.idx_region WHERE region='r0' AND season='road'"
        )[0]
        self.assertEqual(int(result["population"]), 400)
        self.assertEqual(int(result["n_np"]), 2)
        self.assertAlmostEqual(result["hansen_idx"], 25.0)
        self.assertAlmostEqual(result["rai"], 0.25)
        self.assertAlmostEqual(result["share_oecd_remote"], 0.75)
        self.assertAlmostEqual(result["share_city50k_over_1h"], 0.75)
        self.assertAlmostEqual(result["gini"], 0.15)
        self.assertAlmostEqual(result["access_poor_share"], 0.25)
        self.assertAlmostEqual(result["daily_access_pop"], 2500.0)
        self.assertAlmostEqual(result["net_efficiency"], 1.75)
        gaps = store.rows(
            f"SELECT max(abs(seasonal_gap)) gap,max(abs(exposure_manual)) exposure FROM {database}.idx_np_gap"
        )[0]
        self.assertEqual(gaps, {"gap": 0, "exposure": 0})
        before = store.rows(f"SELECT count() n FROM {database}.idx_region")[0]["n"]
        with patch("road_capacity.aggregate.CASE", database):
            rebuild_indices(store, {"poverty_cutoff": 1500.0})
        after = store.rows(f"SELECT count() n FROM {database}.idx_region")[0]["n"]
        self.assertEqual(int(before), 246)
        self.assertEqual(before, after)
