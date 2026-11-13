from fastapi import APIRouter

from app.domain.errors import DataUnavailable
from app.usecase.municipal_scenarios import (
    MunicipalScenarioRequest,
    MunicipalScenarios,
    MunicipalTrafficBaseline,
    MunicipalTrafficEffects,
)
from app.usecase.traffic import TrafficJob


def build_municipal_scenarios_router(scenarios: MunicipalScenarios | None) -> APIRouter:
    router = APIRouter(prefix="/municipal-scenarios", tags=["municipalities"])

    def available() -> MunicipalScenarios:
        if scenarios is None:
            raise DataUnavailable("Municipal traffic baseline storage is not configured")
        return scenarios

    @router.get("/baseline/{region}/{municipality}", response_model=MunicipalTrafficBaseline)
    def baseline(region: str, municipality: str) -> MunicipalTrafficBaseline:
        return available().baseline(region, municipality)

    @router.post("", response_model=TrafficJob)
    def submit(request: MunicipalScenarioRequest) -> TrafficJob:
        return available().submit(request)

    @router.get("/{identifier}", response_model=TrafficJob)
    def get(identifier: str) -> TrafficJob:
        return available().get(identifier)

    @router.get("/{identifier}/effects", response_model=MunicipalTrafficEffects)
    def effects(identifier: str) -> MunicipalTrafficEffects:
        return available().effects(identifier)

    @router.post("/{identifier}/cancel", response_model=TrafficJob)
    def cancel(identifier: str) -> TrafficJob:
        return available().cancel(identifier)

    return router
