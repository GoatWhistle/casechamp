from app.usecase.chat import ChatEvent
from app.usecase.road_corridor import CorridorCalculation, CorridorRegion, RoadCorridor
from app.usecase.road_geometry import RoadGeometry
from app.usecase.road_graph import RoadJob


def road_calculation(job: RoadJob, geometry: RoadGeometry, job_ids: list[str] | None = None) -> ChatEvent:
    corridor = RoadCorridor(
        id=f"scenario-{job.id}",
        road_ref=", ".join(geometry.names),
        origin="",
        destination="",
        way_ids=[change.way_id for change in job.changes],
        length_km=geometry.length_km,
        origin_attachment_km=0,
        destination_attachment_km=0,
        regions=[CorridorRegion(job.region_id, job.region)],
        lines=geometry.lines,
        scope="whole_selected_osm_ways_both_directions",
    )
    return ChatEvent(
        "calculation", calculation=CorridorCalculation(corridor, job_ids or [job.id], job.changes)
    )
