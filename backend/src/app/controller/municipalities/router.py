from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.usecase.municipalities import MunicipalityQueries


class MunicipalityGeometryResponse(BaseModel):
    type: Literal["MultiPolygon"] = "MultiPolygon"
    coordinates: list[list[list[tuple[float, float]]]]


class MunicipalityPropertiesResponse(BaseModel):
    id: str
    name: str
    region_id: str
    admin_level: int
    source_url: str
    observed_at: str
    source_sha256: str
    region_assignment: str
    region_overlap_fraction: float


class MunicipalityFeatureResponse(BaseModel):
    type: Literal["Feature"] = "Feature"
    id: str
    properties: MunicipalityPropertiesResponse
    geometry: MunicipalityGeometryResponse


class MunicipalityMetadataResponse(BaseModel):
    region_id: str
    coverage_status: Literal["available", "unavailable"]
    reason: str | None
    source_url: str | None = None
    observed_at: str | None = None


class MunicipalityCollectionResponse(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[MunicipalityFeatureResponse]
    metadata: MunicipalityMetadataResponse


def build_municipality_router(queries: MunicipalityQueries) -> APIRouter:
    router = APIRouter(tags=["municipalities"])

    @router.get("/regions/{region_id}/municipalities")
    def get_municipalities(region_id: str) -> MunicipalityCollectionResponse:
        result = queries.run(region_id)
        urls = {item.source_url for item in result.items}
        dates = {item.observed_at for item in result.items}
        return MunicipalityCollectionResponse(
            features=[
                MunicipalityFeatureResponse(
                    id=item.id,
                    geometry=MunicipalityGeometryResponse(coordinates=item.coordinates),
                    properties=MunicipalityPropertiesResponse(
                        **{
                            field: getattr(item, field)
                            for field in MunicipalityPropertiesResponse.model_fields
                        }
                    ),
                )
                for item in result.items
            ],
            metadata=MunicipalityMetadataResponse(
                region_id=region_id,
                coverage_status="available" if result.items else "unavailable",
                reason=result.reason,
                source_url=next(iter(urls)) if len(urls) == 1 else None,
                observed_at=next(iter(dates)) if len(dates) == 1 else None,
            ),
        )

    return router
