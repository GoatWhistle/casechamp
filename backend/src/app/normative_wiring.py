from datetime import UTC, datetime

from fastapi import APIRouter

from app.adapter.normative.fire_routing import FireRoutingFactory
from app.adapter.normative.origin_attachment import GraphOriginAttachment
from app.adapter.normative.walking_routing import WalkingNormativeRouting
from app.adapter.road_graph.delta_base import DeltaBase
from app.controller.normative.router import build_normative_router
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.normative import ClickHouseNormativeRepository
from app.repository.clickhouse.pedestrian import ClickHousePedestrianRepository
from app.usecase.normative.interface import NormativeRouting
from app.usecase.normative.queries import NormativeQueries


def build_pilot_normative_router(reader: ClickHouseReader, routing: NormativeRouting | None,
                                 base: DeltaBase | None) -> APIRouter:
    return build_normative_router(NormativeQueries(
        ClickHouseNormativeRepository(reader), routing,
        WalkingNormativeRouting(ClickHousePedestrianRepository(reader, '37000000', 'pilot')),
        FireRoutingFactory(base) if base else None, clock=lambda: datetime.now(UTC),
        object_attachment=GraphOriginAttachment(base) if base else None,
    ))
