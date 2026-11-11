import json
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "work/road-capacity"
API = "http://127.0.0.1:8007/api/v1"


def request(path, body=None):
    payload = json.dumps(body).encode() if body is not None else None
    with urlopen(Request(API + path, data=payload, headers={"Content-Type": "application/json"}), timeout=60) as response:
        return json.load(response)


def calculate(name, body):
    saved = OUTPUT / f"{name}-submitted.json"
    submitted = request("/road-scenarios/" + json.loads(saved.read_text())["id"]) if saved.exists() else request("/road-scenarios", body)
    if submitted["region_id"] != body["region_id"] or submitted["scenario"] != body["scenario"]:
        raise ValueError("Saved live fixture belongs to another scenario")
    expected = body["changes"]
    if len(submitted["changes"]) != len(expected) or any(any(old.get(key) != value for key, value in new.items()) for old, new in zip(submitted["changes"], expected, strict=True)):
        raise ValueError("Saved live fixture uses different road parameters")
    (OUTPUT / f"{name}-submitted.json").write_text(json.dumps(submitted, ensure_ascii=False, indent=2))
    print(name, "submitted", submitted["id"], flush=True)
    start = time.monotonic()
    reported = -1
    while time.monotonic() - start < 900:
        job = request("/road-scenarios/" + submitted["id"])
        if job["status"] in {"completed", "failed", "cancelled"}:
            (OUTPUT / f"{name}-result.json").write_text(json.dumps(job, ensure_ascii=False, indent=2))
            if job["status"] != "completed":
                raise ValueError(f"Live calculation failed: {name}: {job['error']}")
            print(name, "completed", job["result"]["delta"], flush=True)
            return job
        elapsed = int((time.monotonic() - start) // 30)
        if elapsed != reported:
            print(name, job["status"], job["completed"], flush=True)
            reported = elapsed
        time.sleep(2)
    raise TimeoutError("Live calculation did not finish within 900 seconds")


def main():
    fixture = json.loads((OUTPUT / "live-fixture.json").read_text())
    basis = "Synthetic validation assumptions, 2026; not observed traffic or project costs"
    project = {
        "passengers": [{
            "origin_point_id": fixture["origin_point_id"], "market_city": fixture["market_city"],
            "trips_per_year": 100000, "rub_per_hour": 300, "source": basis, "basis": "assumed",
        }],
        "freight": [{
            "name": "Validation road freight", "origin_point_id": fixture["origin_point_id"],
            "market_city": fixture["market_city"], "trips_per_year": 1000,
            "before_hours": None, "after_hours": None, "before_km": None, "after_km": None,
            "rub_per_vehicle_hour": 500, "rub_per_km": 15, "source": basis, "basis": "assumed",
        }],
        "scenarios": [
            {"name": "low", "demand_factor": 0.5, "value_factor": 0.8},
            {"name": "base", "demand_factor": 1, "value_factor": 1},
            {"name": "high", "demand_factor": 1.5, "value_factor": 1.2},
        ],
        "capital_cost_rub": 1000000, "annual_operating_cost_rub": 10000,
        "horizon_years": 20, "discount_rate": 0.05, "price_year": 2026, "cost_source": basis,
    }
    common = {"region_id": fixture["region_id"], "scenario": fixture["scenario"], "appraisal": project}
    lanes = calculate("lanes", {**common, "changes": [{"way_id": identifier, "lanes_total": 4} for identifier in fixture["way_ids"]]})
    result = lanes["result"]
    assert result["road_cost_method"] == "road-capacity-v1"
    assert abs(result["delta"]) < 1e-7
    assert "lanes_without_verified_flow_no_time_effect" in result["road_cost_notes"]
    appraisal = lanes["appraisal_result"]
    assert appraisal["status"] == "calculated"
    assert abs(appraisal["scenarios"][1]["annual_gross_rub"]) < 1e-5
    assert appraisal["freight_routing_scope"] == "road_network_vehicle_constraints_unverified"
    upgraded = calculate("profile", {**common, "changes": [
        {"way_id": identifier, "lanes_total": 4, "highway": "motorway", "surface": "asphalt", "speed_kmh": 90}
        for identifier in fixture["way_ids"]
    ]})
    appraisal = upgraded["appraisal_result"]
    assert upgraded["result"]["delta"] > 0
    assert appraisal["status"] == "calculated"
    travel = appraisal["travel"][0]
    freight = appraisal["freight_travel"][0]
    base = appraisal["scenarios"][1]
    assert travel["after_hours"] < travel["before_hours"]
    assert freight["after_hours"] < freight["before_hours"]
    expected = 1000 * ((freight["before_hours"] - freight["after_hours"]) * 500 + (freight["before_km"] - freight["after_km"]) * 15)
    assert abs(base["annual_freight_rub"] - expected) < 1e-5
    summary = {
        "status": "passed", "basis": basis, "lane_job_id": lanes["id"], "profile_job_id": upgraded["id"],
        "lane_hansen_delta": result["delta"], "lane_annual_gross_rub": lanes["appraisal_result"]["scenarios"][1]["annual_gross_rub"],
        "profile_hansen_delta": upgraded["result"]["delta"], "passenger_travel": travel,
        "freight_travel": freight, "annual_passenger_rub": base["annual_passenger_rub"],
        "annual_freight_rub": base["annual_freight_rub"],
    }
    (ROOT / "docs/results/road-capacity-live-validation.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
