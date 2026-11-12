import json

from app.repository.clickhouse.municipal_revision import municipal_road_revision_matches


def test_road_revision_requires_matching_graph_artifact_and_cost_model() -> None:
    metadata = {
        "graph_revision": "base-graph",
        "artifact_version": "artifact",
        "road_cost_model_version": "road-capacity-v1",
    }
    revision = json.dumps(
        {"base": "base-graph", "artifact": "artifact", "road_cost_model": "road-capacity-v1"}
    )
    assert municipal_road_revision_matches(revision, metadata)
    assert municipal_road_revision_matches(revision, {**metadata, "graph_revision": revision})
    assert not municipal_road_revision_matches(
        revision, {**metadata, "artifact_version": "changed"}
    )
    assert not municipal_road_revision_matches(
        revision, {**metadata, "road_cost_model_version": "changed"}
    )
    assert not municipal_road_revision_matches(revision, {**metadata, "graph_revision": "changed"})
    assert municipal_road_revision_matches("base-graph", metadata)
