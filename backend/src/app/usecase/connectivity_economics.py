import json
from math import isfinite

from app.domain.errors import InvalidQuery


def connectivity_economics(payload: str, value_of_pcu_hour_rub: float = 500) -> str:
    if not isfinite(value_of_pcu_hour_rub) or not 0 < value_of_pcu_hour_rub <= 100000:
        raise InvalidQuery("Supply a positive assumed value in rubles per PCU-hour")
    saved = json.loads(payload)
    if not saved.get("traffic_assumptions"):
        raise InvalidQuery(
            "Saved calculation has no modeled traffic; calculate connectivity with traffic first"
        )
    pairs = []
    for pair in saved["pairs"]:
        loss = pair.get("time_loss_pcu_hours")
        pairs.append(
            {
                "origin": pair["origin"],
                "destination": pair["destination"],
                "time_loss_pcu_hours": loss,
                "time_cost_rub": loss * value_of_pcu_hour_rub if loss is not None else None,
                "complete": loss is not None,
            }
        )
    return json.dumps(
        {
            "calculation_id": saved["calculation_id"],
            "calculated_at": saved["calculated_at"],
            "graph_version": saved["graph_version"],
            "traffic_assumptions": saved["traffic_assumptions"],
            "value_of_pcu_hour_rub": value_of_pcu_hour_rub,
            "value_basis": "explicit_illustrative_composite_rate_not_observed_wages",
            "pairs": pairs,
            "scope": "diverted_cohort_time_cost_only_independent_pairs_do_not_sum",
            "excluded": ["background_traffic_delay", "fuel", "cargo_value", "GDP", "spillback"],
            "method": "saved_diversion_cohort_hours_times_assumed_pcu_hour_value_v1",
        },
        ensure_ascii=False,
        allow_nan=False,
    )
