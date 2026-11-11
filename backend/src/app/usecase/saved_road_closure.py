from app.domain.errors import InvalidQuery
from app.usecase.road_graph import RoadGraph


def saved_closure_ways(roads: RoadGraph, calculation_id: str) -> list[int]:
    job = roads.job(calculation_id)
    if job.version != roads.model_info().version:
        raise InvalidQuery("Saved closure belongs to a different graph version")
    if (
        job.scenario != "road"
        or job.links
        or job.addition
        or not job.changes
        or any(change.speed_factor != 0 for change in job.changes)
    ):
        raise InvalidQuery(
            "Use a saved road-only closure without speed edits, additions or service changes"
        )
    return sorted({change.way_id for change in job.changes})
