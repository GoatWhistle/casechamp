import hashlib
import io
import json
import re

import numpy as np
import pandas as pd
from accessibility.snapshot import SnapshotClient, pin_source
from accessibility.streaming import stream_batches
from analytics.client import ClickHouse
from pyarrow import ipc


class Source:
    def __init__(self, source_revision=None):
        if source_revision is not None and not re.fullmatch(
            "[a-f0-9]{16}", source_revision
        ):
            raise ValueError("Source revision must contain 16 hexadecimal characters")
        self.client = (
            ClickHouse()
            if source_revision is None
            else SnapshotClient("plexus_access_source_" + source_revision)
        )
        self.metadata = self.identity()
        self.revision = hashlib.sha256(
            json.dumps(self.metadata, sort_keys=True).encode()
        ).hexdigest()
        if source_revision is None:
            pinned = pin_source(self.client, self.revision)
            if self.identity() != self.metadata:
                raise ValueError("Source changed while pinning input tables")
            self.client = pinned
        elif self.revision[:16] != source_revision:
            raise ValueError("Pinned source revision does not match its metadata")
        self.assert_unchanged()
        self.regions = self.frame(
            "SELECT oktmo AS region_id,region FROM plexus_graph.region_codes ORDER BY oktmo"
        )
        self.cities = self.frame(
            "SELECT city,oktmo,node,snap_h,population FROM plexus_casechamp.market_cities ORDER BY city"
        )
        self.points = self.frame(
            "SELECT p.point_id AS point_id,p.node AS node,p.snap_km/15 AS snap_h,"
            "coalesce(i.population,0) AS population,i.region AS region "
            "FROM plexus_graph.points p INNER JOIN plexus_casechamp.idx_np i ON p.point_id=i.point_id "
            "WHERE i.season='road' ORDER BY p.point_id"
        )
        self.manual = self.frame(
            "SELECT season,from_id,to_id,mode,kind,travel_h,freq_per_week,freq_assumed "
            "FROM plexus_casechamp.manual_links_ru"
        )
        self.trunk = self.frame(
            "SELECT city_from,city_to,transport_type,distance_hr FROM plexus_casechamp.stg_intercity "
            "WHERE transport_type IN ('rail','air') AND distance_hr IS NOT NULL"
        )
        if self.points.point_id.duplicated().any() or len(self.cities) != 180:
            raise ValueError("Unexpected point or market identifiers")
        if not set(self.regions.region).issubset(set(self.points.region)):
            raise ValueError("Missing regions in calculation origins")
        self.normalization = float(
            self.client.rows(
                "SELECT avg(hansen_2h/hansen*100) AS value FROM plexus_atlas.atlas_indices "
                "WHERE scenario='road' AND hansen>0"
            )[0]["value"]
        )
        if not np.isfinite(self.normalization) or self.normalization <= 0:
            raise ValueError("Invalid normalization")
        self.edges = None
        self.ways = None

    def identity(self):
        meta = self.client.rows(
            "SELECT value FROM plexus_atlas.atlas_metadata WHERE key='graph_revision'"
        )
        versions = self.client.rows(
            "SELECT DISTINCT model_version,artifact_version FROM plexus_atlas.atlas_indices"
        )
        if len(meta) != 1 or len(versions) != 1:
            raise ValueError("One coherent source snapshot is required")
        return dict(versions[0], graph_revision=meta[0]["value"])

    def frame(self, sql):
        return (
            ipc.open_stream(
                io.BytesIO(self.client.request(sql + " FORMAT ArrowStream"))
            )
            .read_all()
            .to_pandas()
        )

    def graph(self):
        if self.edges is None:
            self.edges = self.frame(
                "SELECT src,dst,h,way_idx FROM plexus_graph.edges ORDER BY way_idx,src,dst"
            )
            self.ways = self.frame(
                "SELECT way_idx,is_ferry FROM plexus_graph.ways ORDER BY way_idx"
            )
        return self.edges, self.ways

    def previous(self, season):
        point_ids = self.points.point_id.to_numpy(dtype=str)
        city_names = self.cities.city.to_numpy(dtype=str)
        population = self.points.population.to_numpy(dtype=np.float64)
        markets = self.cities.population.to_numpy(dtype=np.float64)
        regions, names = pd.factorize(self.points.region)
        totals = np.bincount(regions, weights=population)
        sums = np.zeros((3, len(names)))
        sql = (
            "SELECT point_id,city,best_h FROM "
            + self.client.database
            + ".np_city_times "
        )
        sql += (
            "WHERE season={season:String} SETTINGS max_threads=1,max_block_size=32768"
        )
        for batch in stream_batches(self.client, sql, {"season": season}):
            ids = np.asarray(batch["point_id"].to_pylist(), dtype=str)
            cities = np.asarray(batch["city"].to_pylist(), dtype=str)
            points = np.searchsorted(point_ids, ids)
            city = np.searchsorted(city_names, cities)
            if (points >= len(point_ids)).any() or (city >= len(city_names)).any():
                raise ValueError("Unknown origin or market in saved times")
            if not np.array_equal(point_ids[points], ids) or not np.array_equal(
                city_names[city], cities
            ):
                raise ValueError("Saved matrix identifiers do not match the source")
            times = batch["best_h"].to_numpy().astype(np.float64)
            weights = population[points] * markets[city]
            for index, half_life in enumerate((2, 4, 8)):
                sums[index] += np.bincount(
                    regions[points],
                    weights=weights * np.exp(-np.log(2) / half_life * times),
                    minlength=len(names),
                )
        return pd.DataFrame(
            [
                {
                    "region": name,
                    "half_life": h,
                    "value": sums[index, r] / totals[r] / self.normalization * 100,
                }
                for index, h in enumerate((2, 4, 8))
                for r, name in enumerate(names)
            ]
        )

    def assert_unchanged(self):
        if self.identity() != self.metadata:
            raise ValueError(
                "Active source changed during calculation; result was not published"
            )
