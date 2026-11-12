from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Query

from app.controller.normative.regional_view_schemas import (
    RegionalFacilityPageResponse,
    RegionalMapViewResponse,
    RegionalPointDetailResponse,
    RegionalRowPageResponse,
    RegionalRunViewResponse,
)
from app.usecase.normative.regional_view import RegionalMapBounds, RegionalViewQueries, RowSort
from app.usecase.normative.route import RouteStage


def build_regional_view_router(queries: RegionalViewQueries) -> APIRouter:
    router = APIRouter(prefix="/normative", tags=["normative"])

    @router.get(
        "/regions/{region_id}/measurements/{criterion_id}/view",
        response_model=RegionalRunViewResponse | None,
    )
    def latest(region_id: str, criterion_id: str) -> object:
        result = queries.latest(region_id, criterion_id)
        if result is None:
            return None
        return asdict(result)

    @router.get("/regional-measurements/{run_id}/rows", response_model=RegionalRowPageResponse)
    def rows(
        run_id: str,
        stage: RouteStage = "scenario",
        page: Annotated[int, Query(ge=1, le=2147483647)] = 1,
        page_size: Annotated[int, Query(ge=1, le=100)] = 50,
        sort: RowSort = "position",
        descending: bool = False,
        search: Annotated[str, Query(max_length=200)] = "",
    ) -> object:
        return asdict(queries.rows(run_id, stage, page, page_size, sort, descending, search))

    @router.get(
        "/regional-measurements/{run_id}/facilities", response_model=RegionalFacilityPageResponse
    )
    def facilities(
        run_id: str,
        page: Annotated[int, Query(ge=1, le=2147483647)] = 1,
        page_size: Annotated[int, Query(ge=1, le=100)] = 50,
        search: Annotated[str, Query(max_length=200)] = "",
    ) -> object:
        return asdict(queries.facilities(run_id, page, page_size, search))

    @router.get(
        "/regional-measurements/{run_id}/points/{origin_id}",
        response_model=RegionalPointDetailResponse,
    )
    def point(run_id: str, origin_id: str, stage: RouteStage = "scenario") -> object:
        return asdict(queries.point(run_id, stage, origin_id))

    @router.get("/regional-measurements/{run_id}/map", response_model=RegionalMapViewResponse)
    def map_view(
        run_id: str,
        west: float,
        south: float,
        east: float,
        north: float,
        stage: RouteStage = "scenario",
        zoom: Annotated[int, Query(ge=0, le=20)] = 5,
    ) -> object:
        return asdict(
            queries.map_view(run_id, stage, RegionalMapBounds(west, south, east, north), zoom)
        )

    return router
