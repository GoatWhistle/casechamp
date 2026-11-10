from typing import Annotated

from fastapi import APIRouter, Query

from app.controller.atlas.responses import NOT_FOUND
from app.usecase.accessibility import AccessibilityComparison, AccessibilityQueries


def build_accessibility_router(queries: AccessibilityQueries) -> APIRouter:
    router = APIRouter(tags=["accessibility"])

    @router.get(
        "/regions/{region_id}/accessibility",
        responses=NOT_FOUND,
        response_model=AccessibilityComparison,
    )
    def compare(
        region_id: str,
        half_life: Annotated[int, Query(ge=2, le=8)] = 2,
    ) -> AccessibilityComparison:
        return queries.compare(region_id, half_life)

    return router
