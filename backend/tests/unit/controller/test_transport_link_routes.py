from typing import cast
from unittest.mock import Mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.adapter.log.stdlib import StdlibLogger
from app.controller.errors import ErrorHandlers
from app.controller.road_graph.router import build_road_graph_router
from app.usecase.dto import RegionRecord
from app.usecase.interface import AtlasRepository
from app.usecase.road_graph import RoadGraph, RoadGraphPort, RoadJob
from app.usecase.transport_links import LinkChange, PlaceName, TransportLink


def client(port: Mock) -> TestClient:
    atlas = Mock(spec=AtlasRepository)
    atlas.regions.return_value = [RegionRecord("71000000", "ХМАО", 1, 10)]
    app = FastAPI()
    ErrorHandlers(StdlibLogger("test")).register(app)
    app.include_router(build_road_graph_router(RoadGraph(cast(RoadGraphPort, port), atlas)))
    return TestClient(app)


def test_link_only_scenario_is_accepted_and_returned() -> None:
    port = Mock(spec=RoadGraphPort)
    link = LinkChange("remove", "intercity", "air", "Сургут", "*")
    port.submit.return_value = RoadJob(
        "id", "71000000", "ХМАО", "road", [], "queued", 0, 360, "v", links=[link]
    )
    with client(port) as http:
        removal = {
            "action": "remove", "network": "intercity", "mode": "air", "source": "Сургут", "target": "*"
        }
        body: dict[str, object] = {"region_id": "71000000", "links": [removal]}
        response = http.post("/road-scenarios", json=body)
        assert response.status_code == 200
        assert response.json()["links"][0]["target"] == "*"
        port.submit.assert_called_once_with("71000000", "ХМАО", "road", [], [link], queue=False, appraisal=None)
        assert http.post("/road-scenarios", json={"region_id": "71000000"}).status_code == 422
        invalid = {"region_id": "71000000", "links": [{**removal, "mode": "bus"}]}
        assert http.post("/road-scenarios", json=invalid).status_code == 422


def test_new_link_without_hours_is_rejected() -> None:
    port = Mock(spec=RoadGraphPort)
    with client(port) as http:
        response = http.post("/road-scenarios", json={"region_id": "71000000", "links": [
            {"action": "add", "network": "intercity", "mode": "rail", "source": "Москва", "target": "Тверь"}
        ]})
        assert response.status_code == 422
        port.submit.assert_not_called()


def test_transport_link_listing_passes_filters() -> None:
    port = Mock(spec=RoadGraphPort)
    port.transport_links.return_value = [
        TransportLink("intercity", "air", "Сургут", "Сургут", "Москва", "Москва", 3.5)
    ]
    with client(port) as http:
        response = http.get("/transport-links", params={"network": "intercity", "place": "Сургут", "mode": "air"})
        assert response.status_code == 200
        assert response.json()[0]["hours"] == 3.5
        port.transport_links.assert_called_once_with("intercity", "road", "Сургут", "air")


def test_place_names_resolve_point_ids() -> None:
    port = Mock(spec=RoadGraphPort)
    port.place_names.return_value = [PlaceName("98614486101", "село Хоро", "Якутия")]
    with client(port) as http:
        response = http.get("/road-graph/places", params=[("ids", "98614486101"), ("ids", "98614486101")])
        assert response.status_code == 200
        assert response.json()[0]["name"] == "село Хоро"
        port.place_names.assert_called_once_with(["98614486101"])
