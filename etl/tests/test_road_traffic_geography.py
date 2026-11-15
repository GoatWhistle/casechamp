import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from road_traffic.candidates import candidate_roads, coordinate_predicate, literal
from road_traffic.geography import GEOD, RegionCoverage
from road_traffic.matching import match_observations


def boundary(region_id, left, right, bottom=-1, top=1):
    return {
        "id": region_id,
        "name": region_id,
        "polygons": [
            [
                [
                    [left, bottom],
                    [right, bottom],
                    [right, top],
                    [left, top],
                    [left, bottom],
                ]
            ]
        ],
    }


class RegionCoverageTests(unittest.TestCase):
    def test_crossing_regions_conserves_geodesic_length(self):
        coverage = RegionCoverage([boundary("b", 0, 2), boundary("a", -2, 0)])
        result = dict(coverage.measure([[-1, 0], [1, 0]]))
        expected = GEOD.inv(-1, 0, 1, 0)[2] / 1000
        self.assertAlmostEqual(sum(result.values()), expected, places=6)
        self.assertAlmostEqual(result["a"], result["b"], places=6)

    def test_shared_boundary_has_one_deterministic_owner(self):
        coverage = RegionCoverage([boundary("b", 0, 2), boundary("a", -2, 0)])
        self.assertEqual(
            [row[0] for row in coverage.measure([[0, -0.5], [0, 0.5]])], ["a"]
        )

    def test_overlapping_regions_do_not_double_count(self):
        coverage = RegionCoverage([boundary("b", -0.5, 2), boundary("a", -2, 0.5)])
        result = coverage.measure([[-1, 0], [1, 0]])
        self.assertAlmostEqual(
            sum(row[1] for row in result), GEOD.inv(-1, 0, 1, 0)[2] / 1000
        )

    def test_dateline_uses_short_crossing(self):
        coverage = RegionCoverage([boundary("east", 178, -178)])
        result = dict(coverage.measure([[179, 0], [-179, 0]]))
        self.assertAlmostEqual(result["east"], GEOD.inv(179, 0, -179, 0)[2] / 1000)
        self.assertLess(result["east"], 225)

    def test_holes_are_excluded(self):
        region = boundary("a", -2, 2)
        region["polygons"][0].append(
            [[-0.5, -0.5], [0.5, -0.5], [0.5, 0.5], [-0.5, 0.5], [-0.5, -0.5]]
        )
        coverage = RegionCoverage([region])
        result = dict(coverage.measure([[-1, 0], [1, 0]]))
        self.assertAlmostEqual(result["a"], GEOD.inv(-1, 0, 0, 0)[2] / 1000)

    def test_geometry_failure_is_explicit(self):
        with self.assertRaises(ValueError):
            RegionCoverage([{"id": "a", "polygons": []}])
        with self.assertRaises(ValueError):
            RegionCoverage([boundary("a", 0, 2)]).measure([[0, 95], [1, 0]])

    def test_repair_is_reported(self):
        region = {"id": "a", "polygons": [[[[0, 0], [1, 1], [0, 1], [1, 0], [0, 0]]]]}
        self.assertEqual(len(RegionCoverage([region]).repairs), 1)


class ObservationMatchingTests(unittest.TestCase):
    def setUp(self):
        self.observation = {
            "observation_id": "obs",
            "region_id": "r",
            "ref": "М-7",
            "direction": "unknown",
            "lat": 0,
            "lon": 0,
        }
        self.road = {
            "way_id": 1,
            "region_id": "r",
            "ref": "М7",
            "coordinates": [[-0.01, 0], [0.01, 0]],
        }

    def test_matching_coordinate_and_reference_stays_candidate(self):
        result = match_observations([self.observation], [self.road], "v1")
        self.assertEqual(result[0]["status"], "candidate")
        self.assertEqual(result[0]["method"], "road_name_and_coordinates")
        self.assertAlmostEqual(result[0]["distance_m"], 0)

    def test_official_kilometer_without_location_is_unmatched(self):
        result = match_observations(
            [{"observation_id": "obs", "km": 35}], [self.road], "v1"
        )
        self.assertEqual(result[0]["status"], "unmatched")
        self.assertIsNone(result[0]["way_id"])

    def test_manual_confirmation_requires_evidence_and_revision(self):
        confirmation = {
            "observation_id": "obs",
            "way_id": 1,
            "graph_revision": "v1",
            "evidence": "source.pdf p.12 diagram",
        }
        result = match_observations(
            [self.observation], [self.road], "v1", [confirmation]
        )
        self.assertEqual(result[0]["status"], "confirmed")
        self.assertEqual(result[0]["extent"], "point")
        for invalid in [
            {**confirmation, "evidence": ""},
            {**confirmation, "graph_revision": "v2"},
        ]:
            with self.assertRaises(ValueError):
                match_observations([self.observation], [self.road], "v1", [invalid])

    def test_duplicate_road_lines_do_not_duplicate_candidates(self):
        result = match_observations([self.observation], [self.road, self.road], "v1")
        self.assertEqual(len(result), 1)

    def test_confirmation_cannot_point_outside_supplied_roads(self):
        with self.assertRaises(ValueError):
            match_observations(
                [self.observation],
                [],
                "v1",
                [
                    {
                        "observation_id": "obs",
                        "way_id": 1,
                        "graph_revision": "v1",
                        "evidence": "source.pdf p.1",
                    }
                ],
            )

    def test_different_region_does_not_match_name(self):
        result = match_observations(
            [self.observation], [{**self.road, "region_id": "other"}], "v1"
        )
        self.assertEqual(result[0]["status"], "unmatched")


class CandidateSelectionTests(unittest.TestCase):
    def test_queries_are_region_scoped_capped_and_deduplicated(self):
        class Store:
            database = "scratch"

            def __init__(self):
                self.queries = []

            def rows(self, query):
                self.queries.append(query)
                return (
                    [{"way_id": 1, "name": "Road", "coordinates": [[0, 0], [1, 0]]}]
                    if "road_lines" in query
                    else [{"way_id": 1, "ref": "R1"}]
                )

        store = Store()
        obs = {"observation_id": "a", "region_id": "42", "road_name": "Road"}
        roads = candidate_roads(
            store, [obs, {**obs, "observation_id": "b"}], "plexus_traffic_snapshot_test"
        )
        self.assertEqual(len(store.queries), 2)
        self.assertIn("region_id='42'", store.queries[0])
        self.assertIn("run_id='test'", store.queries[0])
        self.assertIn("LIMIT 500", store.queries[0])
        self.assertEqual(roads[0]["ref"], "R1")

    def test_identifier_and_literal_validation(self):
        class Store:
            database = "scratch"

        with self.assertRaises(ValueError):
            candidate_roads(Store(), [], "snapshot;DROP TABLE ways")
        self.assertEqual(literal("a'b\\c"), "'a\\'b\\\\c'")

    def test_dateline_window_is_split(self):
        predicate = coordinate_predicate({"lat": 65, "lon": 179.99})
        self.assertIn("OR", predicate)
        self.assertIn("max_lon>=-180", predicate)
        self.assertNotIn("min_lon<=180.01", predicate)

    def test_same_way_multiple_geometries_keeps_nearest(self):
        observation = {
            "observation_id": "a",
            "region_id": "r",
            "ref": "R1",
            "lat": 0,
            "lon": 0,
        }
        road = {
            "way_id": 1,
            "ref": "R1",
            "region_id": "r",
            "coordinates": [[0, 1], [1, 1]],
        }
        near = {**road, "coordinates": [[-0.01, 0], [0.01, 0]]}
        result = match_observations([observation], [road, near], "v1")
        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result[0]["distance_m"], 0)

    def test_site_street_is_a_candidate_without_confirmation(self):
        observation = {
            "observation_id": "a",
            "region_id": "r",
            "site": "Каквинская (от улицы Кирова)",
        }
        road = {"way_id": 1, "name": "улица Каквинская", "region_id": "r"}
        result = match_observations([observation], [road], "v1")
        self.assertEqual(result[0]["status"], "candidate")


if __name__ == "__main__":
    unittest.main()
