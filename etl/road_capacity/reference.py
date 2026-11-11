import json

import numpy as np

REFERENCE = "plexus_capacity_casechamp.reference_idx_np"


def references(store, output):
    target = output / "reference.json"
    if target.exists():
        return json.loads(target.read_text())
    frame = store.frame(
        f"SELECT population,hansen_2h,hansen_idx,harris,t_aria_a,t_aria_b,t_aria_c,t_aria_d,t_aria_e FROM {REFERENCE} WHERE season='road'"
    )
    positive = frame.hansen_idx > 0
    normalization = float(
        np.mean(
            frame.loc[positive, "hansen_2h"] / frame.loc[positive, "hansen_idx"] * 100
        )
    )
    log_harris = np.log(frame.loc[frame.harris > 0, "harris"])
    valid = frame.population.fillna(0) > 0
    h, population = (
        frame.loc[valid, "hansen_2h"].to_numpy(),
        frame.loc[valid, "population"].to_numpy(dtype=float),
    )
    order = np.argsort(h, kind="stable")
    median = float(
        h[order[np.searchsorted(np.cumsum(population[order]), population.sum() / 2)]]
    )
    result = {
        "normalization_base": normalization,
        "ca_log_min": float(log_harris.min()),
        "ca_log_max": float(log_harris.max()),
        "poverty_cutoff": 0.5 * median,
        "aria_means": {c: float(frame["t_aria_" + c].mean()) for c in "abcde"},
    }
    if not np.isfinite(normalization) or normalization <= 0:
        raise ValueError("Invalid frozen normalization")
    if any(not np.isfinite(v) or v <= 0 for v in result["aria_means"].values()):
        raise ValueError("Invalid frozen ARIA reference")
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return result
