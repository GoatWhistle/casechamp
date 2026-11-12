from synthetic_traffic.project_dedup import deduplicate_projects, physical_key


def connection(**changes):
    return {
        "kind": "connection",
        "source_node": 0,
        "target_node": 1,
        "geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [0.01, 0.0]]},
        "length_km": 1.111950802335329,
        "speed_kmh": 60.0,
        "capacity_vph": 1800.0,
        **changes,
    }


def test_exact_duplicates_merge_full_provenance_without_mutating_inputs():
    a = {
        "kind": "capacity",
        "way_ids": [2, 1],
        "extra_lanes": 1,
        "target_origin": "index_route",
    }
    b = {
        "kind": "capacity",
        "way_ids": [1, 2],
        "extra_lanes": 1,
        "target_origin": "agent_hypothesis",
    }
    rows, removed = deduplicate_projects([a, b])
    assert removed == 1 and len(rows) == 1
    assert {p["target_origin"] for p in rows[0]["source_provenance"]} == {
        "index_route",
        "agent_hypothesis",
    }
    assert len(rows[0]["equivalent_proposals"]) == 2
    assert "source_provenance" not in a and "source_provenance" not in b


def test_reversed_and_duplicate_vertex_geometry_is_same_physical_intervention():
    a = connection()
    b = connection(
        source_node=1,
        target_node=0,
        geometry={
            "type": "LineString",
            "coordinates": [[0.01, 0.0], [0.01, 0.0], [0.0, 0.0]],
        },
    )
    assert physical_key(a) == physical_key(b)
    assert len(deduplicate_projects([a, b])[0]) == 1


def test_distinct_curves_capacity_and_intervention_kinds_are_preserved():
    base = connection()
    variants = [
        base,
        connection(capacity_vph=3600),
        connection(speed_kmh=40),
        connection(kind="opening", source_reference="official-road"),
        connection(
            geometry={
                "type": "LineString",
                "coordinates": [[0.0, 0.0], [0.005, 1e-8], [0.01, 0.0]],
            }
        ),
    ]
    rows, removed = deduplicate_projects(variants)
    assert removed == 0 and len(rows) == len(variants)


def test_package_order_deduplicates_and_retains_child_sources():
    a = {"kind": "capacity", "way_ids": [1], "target_origin": "index_route"}
    b = {"kind": "closure", "way_ids": [2]}
    alternate = {**a, "target_origin": "agent_hypothesis"}
    rows, removed = deduplicate_projects(
        [
            {"kind": "package", "projects": [a, b]},
            {"kind": "package", "projects": [b, alternate]},
        ]
    )
    assert removed == 1 and len(rows) == 1
    lane = next(part for part in rows[0]["projects"] if part["kind"] == "capacity")
    assert {p["target_origin"] for p in lane["source_provenance"]} == {
        "index_route",
        "agent_hypothesis",
    }


def test_dependent_packages_keep_order_and_multiplicity():
    road = connection()
    extra = {"kind": "capacity", "way_ids": [-1], "extra_lanes": 1}
    original = {"kind": "package", "projects": [road, extra]}
    reverse = {"kind": "package", "projects": [extra, road]}
    rows, removed = deduplicate_projects([original, reverse])
    assert removed == 0
    assert rows[0]["projects"] == [road, extra]
    repeated = {
        "kind": "package",
        "projects": [
            {"kind": "capacity", "way_ids": [1]},
            {"kind": "capacity", "way_ids": [1]},
        ],
    }
    assert physical_key(repeated) is None
    assert len(deduplicate_projects([repeated])[0][0]["projects"]) == 2
