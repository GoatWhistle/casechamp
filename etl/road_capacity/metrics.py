import numpy as np

THRESHOLDS = {"a": 250000, "b": 48000, "c": 18000}


def min_hours(matrix, selected):
    return (
        matrix[:, selected].min(axis=1)
        if np.any(selected)
        else np.full(len(matrix), np.inf)
    )


def point_metrics(origins, road, best, cities, local, reference):
    result = origins.copy()
    result["reachable_markets"] = np.isfinite(best).sum(axis=1)
    population = np.array([row[3] for row in cities], dtype=float)
    for half_life in [1, 2, 4]:
        result[f"hansen_{half_life}h"] = (
            np.exp(-np.log(2) / half_life * best.astype(float)) @ population
        )
    result["hansen_idx"] = result.hansen_2h / reference["normalization_base"] * 100
    result["harris"] = (1 / (best.astype(float) + 0.5)) @ population
    low, high = reference["ca_log_min"], reference["ca_log_max"]
    harris = result.harris.to_numpy(dtype=float)
    logged = np.log(np.maximum(harris, np.finfo(float).tiny))
    result["remoteness_ca"] = np.clip(1 - (logged - low) / (high - low), 0, 1)
    for hour in [1, 2, 4]:
        result[f"cum_pop_{hour}h"] = (best <= hour) @ population
    result["t_city50k_road_h"] = min_hours(road, population >= 50000)
    result["t_city50k_best_h"] = min_hours(best, population >= 50000)
    result["oecd_remote"] = result.t_city50k_road_h > 1
    for key, threshold in THRESHOLDS.items():
        result["t_aria_" + key] = min_hours(best, population >= threshold)
    result["t_aria_c"] = np.fmin(result.t_aria_c.to_numpy(), local["t_centre_18k_h"])
    result["t_aria_d"] = local["t_centre_5k_h"]
    result["t_aria_e"] = local["t_centre_1k_h"]
    aria = np.zeros(len(result))
    for key in "abcde":
        ratio = (
            result["t_aria_" + key].to_numpy(dtype=float) / reference["aria_means"][key]
        )
        aria += np.minimum(np.where(np.isnan(ratio), 3.0, ratio), 3.0)
    result["aria"] = aria
    result["aria_class"] = np.array(
        ["major_city", "inner_regional", "outer_regional", "remote", "very_remote"]
    )[np.searchsorted([0.2, 2.4, 5.92, 10.53], aria, side="left")]
    result["t_district_center_h"] = local["t_district_center_h"]
    result["lancet_2h"] = result.t_district_center_h <= 2
    for name in [
        "t_city50k_road_h",
        "t_city50k_best_h",
        "t_aria_a",
        "t_aria_b",
        "t_aria_c",
        "t_aria_d",
        "t_aria_e",
    ]:
        result[name] = result[name].where(np.isfinite(result[name]))
    return result


def network_efficiency(best, origins, market_coordinates, populations):
    lat, lon = (
        np.radians(origins["lat"].to_numpy(dtype=float)),
        np.radians(origins["lon"].to_numpy(dtype=float)),
    )
    city_lat, city_lon = (
        np.radians(market_coordinates[:, 0]),
        np.radians(market_coordinates[:, 1]),
    )
    a = (
        np.sin((city_lat[None, :] - lat[:, None]) / 2) ** 2
        + np.cos(lat[:, None])
        * np.cos(city_lat[None, :])
        * np.sin((city_lon[None, :] - lon[:, None]) / 2) ** 2
    )
    km = 12742 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    valid = (km >= 10) & np.isfinite(best)
    weighted = np.where(valid, best / np.maximum(km / 90, 1e-12), 0) * populations
    denominator = valid @ populations
    return np.divide(
        weighted.sum(axis=1),
        denominator,
        out=np.full(len(best), np.nan),
        where=denominator > 0,
    )
