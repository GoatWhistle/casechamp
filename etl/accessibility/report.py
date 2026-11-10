import numpy as np
from app.domain.accessibility import HALF_LIVES, access_by_half_life


def regional_values(source, best):
    markets = source.cities.population.to_numpy(dtype=np.float64)
    population = (
        source.points.population.fillna(0).clip(lower=0).to_numpy(dtype=np.float64)
    )
    output = {}
    for half_life in HALF_LIVES:
        access = access_by_half_life(best, markets, half_life)
        for region in source.regions.itertuples():
            selected = (source.points.region == region.region).to_numpy()
            total = float(population[selected].sum())
            if total <= 0:
                raise ValueError("Positive regional population required")
            value = float(
                access[selected]
                @ population[selected]
                / total
                / source.normalization
                * 100
            )
            coverage = float(
                population[selected & np.isfinite(best).any(axis=1)].sum() / total
            )
            output[(region.region_id, half_life)] = (value, coverage, int(total))
    return output


def frequencies(source):
    records = []
    for season in ("summer", "winter"):
        for mode in ("air", "rail"):
            rows = source.trunk[source.trunk.transport_type == mode]
            records.append(
                {
                    "season": season,
                    "mode": mode,
                    "source": "trunk",
                    "total": len(rows),
                    "known": 0,
                }
            )
        for mode in ("air", "river", "ferry"):
            rows = source.manual[
                (source.manual.season == season) & (source.manual["mode"] == mode)
            ]
            known = (rows.freq_per_week.gt(0) & ~rows.freq_assumed.fillna(True)).sum()
            records.append(
                {
                    "season": season,
                    "mode": mode,
                    "source": "local",
                    "total": len(rows),
                    "known": int(known),
                }
            )
        _, ways = source.graph()
        records.append(
            {
                "season": season,
                "mode": "ferry",
                "source": "osm",
                "total": int(ways.is_ferry.sum()),
                "known": 0,
            }
        )
    return records


def assemble(source, season, values, previous):
    old = {(r.region, int(r.half_life)): float(r.value) for r in previous.itertuples()}
    names = dict(zip(source.regions.region_id, source.regions.region))
    rows = []
    for key, (potential, coverage, population) in values["full"].items():
        region, half_life = key
        without = {mode: values[mode][key][0] for mode in ("air", "rail", "water")}
        if any(
            value > potential + max(1e-7, potential * 1e-7)
            for value in without.values()
        ):
            raise ValueError("Removing a mode increased accessibility")
        previous_value = old[(names[region], half_life)]
        rows.append(
            {
                "region_id": region,
                "season": season,
                "half_life": half_life,
                "previous": previous_value,
                "potential": potential,
                "delta": potential - previous_value,
                "without_air": without["air"],
                "without_rail": without["rail"],
                "without_water": without["water"],
                "population": population,
                "population_coverage": coverage,
            }
        )
    return rows
