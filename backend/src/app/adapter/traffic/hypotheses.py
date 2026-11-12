from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq
from synthetic_traffic.model import Network

from app.domain.errors import InvalidQuery
from app.usecase.traffic import TrafficHypothesis


def resolve_hypotheses(
    hypotheses: list[TrafficHypothesis], path: Path, network: Network
) -> list[dict[str, Any]]:
    if not hypotheses:
        return []
    rows = pq.read_table(path / "places.parquet").to_pylist()
    result = []
    seen = set()
    for hypothesis in hypotheses:
        nodes = []
        for place in (hypothesis.source_place, hypothesis.target_place):
            exact = [r for r in rows if str(r["point_id"]).casefold() == place.casefold()]
            matched = exact or [
                r for r in rows if str(r["settlement"]).casefold() == place.casefold()
            ]
            if len(matched) != 1:
                raise InvalidQuery(
                    "Hypothesis place is missing or ambiguous; use a stored settlement ID"
                )
            node = int(matched[0]["node"])
            position = int(np.searchsorted(network.raw_nodes, node))
            if position >= len(network.raw_nodes) or int(network.raw_nodes[position]) != node:
                raise InvalidQuery("Hypothesis endpoint lies outside the selected road network")
            nodes.append(node)
        if nodes[0] == nodes[1]:
            raise InvalidQuery("Hypothesis endpoints must resolve to different road nodes")
        key = tuple(sorted(nodes))
        if key not in seen:
            seen.add(key)
            result.append(
                {
                    "source_node": nodes[0],
                    "target_node": nodes[1],
                    "reason": hypothesis.rationale,
                    "origin": "agent_hypothesis",
                    "source_place": hypothesis.source_place,
                    "target_place": hypothesis.target_place,
                }
            )
    return result
