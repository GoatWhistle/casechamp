from dataclasses import asdict

from fastapi import APIRouter
from pydantic import BaseModel

from app.controller.normative.router import FacilityResponse
from app.usecase.normative.regional_catalog import RegionalCatalogQueries


class RegionalCatalogResponse(BaseModel):
    region_id: str
    region_name: str
    criterion_id: str
    category: str
    facilities: list[FacilityResponse]
    candidate_count: int
    walking_measurement_available: bool
    emergency_measurement_available: bool
    road_measurement_available: bool
    calculation_available: bool
    profile_verification: str


def build_regional_catalog_router(queries: RegionalCatalogQueries) -> APIRouter:
    router = APIRouter(prefix="/normative", tags=["normative"])

    @router.get(
        "/regions/{region_id}/catalog/{criterion_id}", response_model=RegionalCatalogResponse
    )
    def catalog(region_id: str, criterion_id: str) -> object:
        return asdict(queries.catalog(region_id, criterion_id))

    return router
