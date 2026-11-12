import numpy as np


def ranking_metrics(x, y, predictions, groups, mask):
    records = []
    for group in np.unique(groups[mask]):
        selected = mask & (groups == group)
        values, estimates = y[selected], predictions[selected]
        order = np.argsort(-estimates, kind="stable")
        baseline = int(np.argmax(x[selected, 18]))
        records.append(
            {
                "group": int(group),
                "samples": int(selected.sum()),
                "selected_gain": float(values[order[0]]),
                "top3_best_gain": float(values[order[:3]].max()),
                "deterministic_gain": float(values[baseline]),
                "oracle_gain": float(values.max()),
                "top1_regret": float(values.max() - values[order[0]]),
            }
        )
    return {
        "samples": int(mask.sum()),
        "mae": float(np.abs(predictions[mask] - y[mask]).mean())
        if mask.any()
        else None,
        "zero_mae": float(np.abs(y[mask]).mean()) if mask.any() else None,
        "rankings": records,
        "selected_mean_gain": float(np.mean([r["selected_gain"] for r in records]))
        if records
        else None,
        "oracle_mean_gain": float(np.mean([r["oracle_gain"] for r in records]))
        if records
        else None,
    }
