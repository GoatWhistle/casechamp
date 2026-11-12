from dataclasses import asdict

from pydantic_ai import ModelRetry, RunContext

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.connectivity_reply import connectivity_reply
from app.adapter.chat.scenario_requests import ConnectivityScenario
from app.domain.errors import DomainError
from app.usecase.chat_artifacts import ChatCell, ChatColumn, ChatTable
from app.usecase.road_corridor import RoadCorridors


def calculate_connectivity(
    ctx: RunContext[ChatRun],
    corridors: RoadCorridors,
    request: ConnectivityScenario,
) -> str:
    try:
        result = corridors.connectivity(
            request.places,
            request.mode,
            request.center,
            request.selection_ids,
            None,
        )
    except DomainError as error:
        raise ModelRetry(error.message) from error
    summary: dict[str, ChatCell] = {
        "id": result.calculation_id,
        "calculation_id": result.calculation_id,
        "score_before": result.score_before,
        "score_after": result.score_after,
        "delta": result.delta,
        "reachable_before": result.reachable_before,
        "reachable_after": result.reachable_after,
        "pair_count": len(result.pairs),
        "disconnected_pairs": result.disconnected_pairs,
        "unbound_pairs": result.unbound_pairs,
        "graph_version": result.graph_version,
        "model_version": result.model_version,
        "connectivity_mode": result.mode,
        "assumed_utilization": result.traffic_assumptions.utilization
        if result.traffic_assumptions
        else None,
        "duration_hours": result.traffic_assumptions.duration_hours
        if result.traffic_assumptions
        else None,
    }
    source = "model:" + result.model_version + ":" + result.graph_version
    ctx.deps.table(
        ChatTable(
            "",
            "connectivity_summary",
            tuple(ChatColumn(key, "number") for key in ("score_before", "score_after", "delta"))
            + (ChatColumn("disconnected_pairs", "integer"),),
            (summary,),
            1,
            False,
            source,
        )
    )
    rows: list[dict[str, ChatCell]] = []
    for pair in result.pairs:
        rows.append(
            {
                "id": pair.origin.id + ":" + pair.destination.id,
                "origin": pair.origin.name + ", " + pair.origin.region,
                "destination": pair.destination.name + ", " + pair.destination.region,
                "hours_before": pair.before.hours,
                "hours_after": pair.after.hours,
                "status_before": pair.before.status,
                "status_after": pair.after.status,
                "score_before": pair.score_before,
                "score_after": pair.score_after,
                "delta": pair.delta,
                "flow_pcu_h": pair.traffic.displaced_flow_pcu_h if pair.traffic else None,
                "queue_pcu": pair.traffic.queue_at_end_pcu if pair.traffic else None,
                "time_loss_pcu_hours": pair.time_loss_pcu_hours,
            }
        )
    ctx.deps.table(
        ChatTable(
            "",
            "connectivity",
            (
                ChatColumn("origin"),
                ChatColumn("destination"),
                ChatColumn("hours_before", "number"),
                ChatColumn("hours_after", "number"),
                ChatColumn("status_before"),
                ChatColumn("status_after"),
                ChatColumn("score_before", "number"),
                ChatColumn("score_after", "number"),
            )
            + (
                (
                    ChatColumn("flow_pcu_h", "number"),
                    ChatColumn("queue_pcu", "number"),
                    ChatColumn("time_loss_pcu_hours", "number"),
                )
                if result.traffic_assumptions
                else ()
            ),
            tuple(rows),
            len(rows),
            False,
            source,
        )
    )
    return connectivity_reply(asdict(result))
