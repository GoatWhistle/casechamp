import numpy as np
import pyarrow as pa
from inequality import gini, palma, theil

CASE = "plexus_capacity_casechamp"


def expressions():
    weight = "sum(n.population)"
    average = lambda field: f"sum(n.population*n.{field})/nullIf({weight},0)"
    share = lambda condition: f"sumIf(n.population,{condition})/nullIf({weight},0)"
    return {
        "population": weight,
        "n_np": "count()",
        **{
            name: average(name)
            for name in [
                "hansen_idx",
                "hansen_1h",
                "hansen_2h",
                "hansen_4h",
                "remoteness_ca",
                "aria",
            ]
        },
        "daily_access_pop": average("cum_pop_4h"),
        "share_oecd_remote": share("n.oecd_remote"),
        "share_city50k_over_1h": share(
            "n.t_city50k_best_h>1 OR n.t_city50k_best_h IS NULL"
        ),
        "share_lancet_2h": share("n.lancet_2h"),
        "rai": "sumIf(n.population,n.is_rural AND n.rai_2km)/nullIf(sumIf(n.population,n.is_rural),0)",
        "net_efficiency": "sum(n.population*n.net_efficiency)/nullIf(sumIf(n.population,n.net_efficiency IS NOT NULL),0)",
        "share_aria_remote": share("n.aria_class IN ('remote','very_remote')"),
        "pop_no_capital": "sumIf(n.population,n.t_capital_best_h IS NULL)",
        "covered_population": "sumIf(n.population,n.hansen_2h>0)",
        "covered_settlements": "countIf(n.hansen_2h>0)",
        "oecd_remote_region": share("n.oecd_remote") + ">0.5",
        **{name: "NULL" for name in ["gini", "palma", "theil", "access_poor_share"]},
    }


def grouped(store, name, keys):
    target = CASE + "." + name
    loading = store.fresh(target)
    fields = [row["name"] for row in store.rows(f"DESCRIBE TABLE {target}")]
    formulae = expressions()
    values = [
        "n." + field if field in keys else formulae[field] + " AS " + field
        for field in fields
    ]
    store.execute(
        f"INSERT INTO {loading} SELECT {','.join(values)} FROM {CASE}.idx_np n GROUP BY {','.join('n.' + key for key in keys)}"
    )
    store.replace(loading, target)


def inequality_indices(store, reference):
    points = store.frame(
        f"SELECT season,region,population,hansen_2h FROM {CASE}.idx_np WHERE population>0"
    )
    regional = store.frame(f"SELECT * FROM {CASE}.idx_region")
    totals = []
    for season, population in points.groupby("season"):
        x = population.hansen_2h.to_numpy(dtype=float)
        w = population.population.to_numpy(dtype=float)
        mean = np.average(x, weights=w)
        total_theil = theil(x, w) if mean > 0 else np.nan
        between = 0.0
        for region, group in population.groupby("region"):
            values = group.hansen_2h.to_numpy(dtype=float)
            weights = group.population.to_numpy(dtype=float)
            average = np.average(values, weights=weights)
            if average > 0 and mean > 0:
                between += (
                    weights.sum() / w.sum() * average / mean * np.log(average / mean)
                )
            selected = (regional.season == season) & (regional.region == region)
            for field, value in {
                "gini": gini(values, weights) if average > 0 else np.nan,
                "palma": palma(values, weights),
                "theil": theil(values, weights) if average > 0 else np.nan,
                "access_poor_share": weights[values < reference["poverty_cutoff"]].sum()
                / weights.sum(),
            }.items():
                regional.loc[selected, field] = value
        totals.append(
            {
                "season": season,
                "theil": total_theil,
                "between_regions": between,
                "within_regions": total_theil - between,
                "gini": gini(x, w) if mean > 0 else np.nan,
                "palma": palma(x, w),
                "access_poor_share": w[x < reference["poverty_cutoff"]].sum() / w.sum(),
            }
        )
    for name, values in [
        ("idx_region", pa.Table.from_pandas(regional, preserve_index=False)),
        ("idx_theil", pa.Table.from_pylist(totals)),
    ]:
        target = CASE + "." + name
        loading = store.fresh(target)
        store.insert_arrow(loading, values)
        store.replace(loading, target)


def gaps(store):
    target = CASE + ".idx_np_gap"
    loading = store.fresh(target)
    store.execute(f"""INSERT INTO {loading} SELECT p.point_id,p.name,p.region,p.mun_upper,p.population,
        p.road,p.summer,p.winter,1-p.road/nullIf(greatest(p.summer,p.winter),0),
        1-least(p.summer,p.winter)/nullIf(greatest(p.summer,p.winter),0),
        if(p.summer>=p.winter,'summer','winter')
        FROM (SELECT point_id,any(name) name,any(region) region,any(mun_upper) mun_upper,any(population) population,
        maxIf(hansen_2h,season='road') road,maxIf(hansen_2h,season='summer') summer,
        maxIf(hansen_2h,season='winter') winter FROM {CASE}.idx_np GROUP BY point_id) p""")
    store.replace(loading, target)


def rebuild_indices(store, reference):
    grouped(store, "idx_mo", ["season", "region", "mun_upper"])
    grouped(store, "idx_region", ["season", "region"])
    inequality_indices(store, reference)
    gaps(store)
    rows = store.rows(
        f"SELECT season,count() regions FROM {CASE}.idx_region GROUP BY season ORDER BY season"
    )
    expected = int(
        store.rows(f"SELECT uniqExact(region) n FROM {CASE}.reference_idx_region")[0][
            "n"
        ]
    )
    if len(rows) != 3 or any(int(row["regions"]) != expected for row in rows):
        raise ValueError(
            "Candidate indices do not cover Atlas82 and all three legacy scenarios"
        )
    return rows
