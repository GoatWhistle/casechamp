import json
from typing import cast
from unittest.mock import Mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.adapter.chat.traffic_tools import traffic_event, traffic_reply
from app.controller.traffic.router import build_traffic_router
from app.usecase.traffic import TrafficJob, TrafficPort, TrafficScope
from app.usecase.traffic_evidence import public_traffic_job


def example() -> TrafficJob:
    return TrafficJob(
        "stored",
        TrafficScope(),
        provenance=json.dumps({
            "verified_observations": [{"gain": -0.1, "project": {"kind": "closure"}}],
            "verified_projects": 1,
            "generated_vehicles_per_hour": 100,
        }),
    )


def test_projection_hides_training_records_without_mutating_stored_job() -> None:
    job = example()
    public = public_traffic_job(job)
    assert "verified_observations" not in json.loads(public.provenance)
    assert json.loads(public.provenance)["verified_projects"] == 1
    assert json.loads(job.provenance)["verified_observations"][0]["gain"] == -0.1
    assert public_traffic_job(public) is public
    event = traffic_event(job)
    assert event.traffic is not None
    assert event.traffic.provenance == public.provenance
    assert json.loads(traffic_reply(job, full=True))["provenance"] == public.provenance


def test_ordinary_provenance_retains_exact_representation() -> None:
    job = TrafficJob("plain", TrafficScope(), provenance='{"precise": 1.234567890123}')
    assert public_traffic_job(job) is job


def test_http_list_detail_submit_and_cancel_hide_training_records() -> None:
    job = example()
    port = Mock(spec=TrafficPort)
    port.submit.return_value = port.get.return_value = port.cancel.return_value = job
    port.recent.return_value = [job]
    app = FastAPI()
    app.include_router(build_traffic_router(cast(TrafficPort, port)))
    with TestClient(app) as client:
        responses = [
            client.get("/traffic-jobs"),
            client.get("/traffic-jobs/stored"),
            client.post("/traffic-jobs", json={}),
            client.post("/traffic-jobs/stored/cancel"),
        ]
    for response in responses:
        assert response.status_code == 200
        body = response.json()
        item = body[0] if isinstance(body, list) else body
        evidence = json.loads(item["provenance"])
        assert "verified_observations" not in evidence
        assert evidence["verified_projects"] == 1
    assert "verified_observations" in json.loads(job.provenance)
