from types import SimpleNamespace

import numpy as np
from synthetic_traffic.project_packages import complementary_packages


def test_packages_skip_conflicts_and_prioritize_connected_complements():
    network = SimpleNamespace(
        source=np.array([0, 1, 3]),
        target=np.array([1, 2, 4]),
        raw_nodes=np.arange(5),
        way_id=np.array([1, 2, 3]),
    )
    rows = [
        {"kind": "capacity", "way_ids": [1]},
        {"kind": "capacity", "way_ids": [3]},
        {"kind": "capacity", "way_ids": [2]},
        {"kind": "closure", "way_ids": [1]},
    ]
    packages, rejected = complementary_packages(network, rows, 4)
    assert rejected >= 1
    first = packages[0]["projects"]
    assert {way for row in first for way in row["way_ids"]} == {1, 2}
    assert not any(
        {row["kind"] for row in package["projects"]} == {"capacity", "closure"}
        and all(row["way_ids"] == [1] for row in package["projects"])
        for package in packages
    )


def test_zero_package_budget_does_not_scan_network_or_candidate_pairs():
    assert complementary_packages(None, [{"kind": "unsupported"}], 0) == ([], 0)
