from typing import Annotated, Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.domain.appraisal_inputs import ProjectAssumptions
from app.domain.road_economics import MoneyAssumptions
from app.usecase.road_graph import (
    GraphLocation,
    RoadAddition,
    RoadChange,
    RoadGraph,
    RoadJob,
    RoadView,
)
from app.usecase.transport_links import LinkChange, PlaceName, TransportLink


class RoadChangeInput(BaseModel):
    way_id: int = Field(ge=0)
    speed_factor: float = Field(default=1, ge=0, le=3)
    lanes_total: int | None = Field(default=None, ge=1, le=32)
    highway: str | None = Field(default=None, max_length=40)
    surface: str | None = Field(default=None, max_length=40)
    speed_kmh: float | None = Field(default=None, gt=0, le=200)


class LinkChangeInput(BaseModel):
    action: Literal["add", "remove"]
    network: Literal["intercity", "local"]
    mode: Literal["rail", "air", "river", "ferry", "winter_road", "ice_crossing", "pontoon_bridge"]
    source: str = Field(min_length=1, max_length=100)
    target: str = Field(min_length=1, max_length=100)
    hours: float | None = Field(default=None, gt=0, le=72)


class RoadScenarioInput(BaseModel):
    region_id: str = Field(min_length=1, max_length=64)
    scenario: Literal["road", "summer", "winter"] = "road"
    changes: list[RoadChangeInput] = Field(default_factory=list, max_length=50)
    links: list[LinkChangeInput] = Field(default_factory=list, max_length=30)
    appraisal: ProjectAssumptions | None = None


class RoadAdditionInput(BaseModel):
    region_id: str = Field(min_length=1, max_length=64)
    source_node: int = Field(ge=0)
    target_node: int = Field(ge=0)
    travel_hours: float = Field(gt=0, le=72)
    money: MoneyAssumptions | None = None
    appraisal: ProjectAssumptions | None = None


def build_road_graph_router(graph: RoadGraph) -> APIRouter:
    router = APIRouter(tags=["road-graph"])

    @router.get("/road-graph/markets", response_model=list[str])
    def markets() -> list[str]:
        return graph.markets()

    @router.get("/road-graph/locations", response_model=list[GraphLocation])
    def locations(query: str, region_id: str | None = None) -> list[GraphLocation]:
        return graph.locations(query, region_id)

    @router.get("/road-graph", response_model=RoadView)
    def view(west: float, south: float, east: float, north: float, zoom: float = 8) -> RoadView:
        return graph.view(west, south, east, north, zoom)

    @router.post("/road-connections", response_model=RoadJob)
    def add_connection(body: RoadAdditionInput) -> RoadJob:
        return graph.add_connection(
            body.region_id,
            RoadAddition(body.source_node, body.target_node, body.travel_hours),
            body.money,
            body.appraisal,
        )

    @router.get("/transport-links", response_model=list[TransportLink])
    def transport_links(
        network: Literal["intercity", "local"],
        place: str,
        scenario: Literal["road", "summer", "winter"] = "road",
        mode: str | None = None,
    ) -> list[TransportLink]:
        return graph.transport_links(network, scenario, place, mode)

    @router.get("/road-graph/places", response_model=list[PlaceName])
    def place_names(ids: Annotated[list[str], Query()]) -> list[PlaceName]:
        return graph.place_names(ids)

    @router.get("/road-scenarios", response_model=list[RoadJob])
    def recent() -> list[RoadJob]:
        return graph.recent()

    @router.post("/road-scenarios", response_model=RoadJob)
    def submit(body: RoadScenarioInput) -> RoadJob:
        return graph.submit(
            body.region_id,
            body.scenario,
            [RoadChange(**c.model_dump()) for c in body.changes],
            [LinkChange(**link.model_dump()) for link in body.links],
            appraisal=body.appraisal,
        )

    @router.get("/road-scenarios/{job_id}", response_model=RoadJob)
    def job(job_id: str) -> RoadJob:
        return graph.job(job_id)

    @router.delete("/road-scenarios/{job_id}", response_model=RoadJob)
    def cancel(job_id: str) -> RoadJob:
        return graph.cancel(job_id)

    return router
