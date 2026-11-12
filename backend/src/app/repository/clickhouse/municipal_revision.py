import json


def municipal_road_revision_matches(revision: str, metadata: dict[str, str]) -> bool:
    try:
        record = json.loads(revision)
    except (ValueError, TypeError):
        return revision == metadata.get("graph_revision")
    if not isinstance(record, dict):
        return revision == metadata.get("graph_revision")
    expected_base = metadata.get("graph_revision")
    try:
        expected_record = json.loads(expected_base or "")
        if isinstance(expected_record, dict):
            expected_base = expected_record.get("base")
    except (ValueError, TypeError):
        pass
    return (
        record.get("base") == expected_base
        and record.get("artifact") == metadata.get("artifact_version")
        and record.get("road_cost_model") == metadata.get("road_cost_model_version")
    )
