from dataclasses import dataclass
from typing import Literal

from app.domain.connectivity import PairAccess, group_score, pair_score
from app.domain.errors import InvalidQuery
from app.domain.traffic_diversion import DiversionResult, TrafficAssumptions

ConnectivityMode = Literal["all_pairs", "to_center"]


@dataclass(frozen=True)
class ConnectivityPlace:
    id: str
    name: str
    region: str


@dataclass(frozen=True)
class ConnectivityPair:
    origin: ConnectivityPlace
    destination: ConnectivityPlace
    before: PairAccess
    after: PairAccess
    score_before: float | None
    score_after: float | None
    delta: float | None
    traffic: DiversionResult | None = None
    time_loss_pcu_hours: float | None = None


@dataclass(frozen=True)
class ConnectivityResult:
    places: list[ConnectivityPlace]
    mode: ConnectivityMode
    center_id: str | None
    pairs: list[ConnectivityPair]
    score_before: float | None
    score_after: float | None
    delta: float | None
    reachable_before: int
    reachable_after: int
    disconnected_pairs: int
    unbound_pairs: int
    closed_way_ids: list[int]
    graph_version: str
    model_version: str = "selected-settlements-road-v1"
    half_life_hours: float = 2
    network: str = "baseline_roads_undirected"
    calculation_id: str = ""
    calculated_at: str = ""
    traffic_assumptions: TrafficAssumptions | None = None


def validate_selection(places: list[str], mode: str, center: str | None) -> None:
    if not 2 <= len(places) <= 12 or any(not 2 <= len(p.strip()) <= 150 for p in places):
        raise InvalidQuery("Select 2 to 12 settlements with names and optional regions")
    if len({p.strip().casefold() for p in places}) != len(places):
        raise InvalidQuery("Select distinct settlements")
    if mode not in {"all_pairs", "to_center"}:
        raise InvalidQuery("Choose all_pairs or to_center")
    if (mode == "to_center" and center not in places) or (mode == "all_pairs" and center):
        raise InvalidQuery("For to_center specify the center exactly as one selected settlement")


def connectivity_pair(
    origin: ConnectivityPlace,
    destination: ConnectivityPlace,
    before: PairAccess,
    after: PairAccess,
) -> ConnectivityPair:
    initial, final = pair_score(before), pair_score(after)
    delta = final - initial if initial is not None and final is not None else None
    return ConnectivityPair(origin, destination, before, after, initial, final, delta)


def connectivity_result(
    places: list[ConnectivityPlace],
    mode: ConnectivityMode,
    center_id: str | None,
    pairs: list[ConnectivityPair],
    closed_way_ids: list[int],
    graph_version: str,
) -> ConnectivityResult:
    before = group_score([pair.before for pair in pairs])
    after = group_score([pair.after for pair in pairs])
    return ConnectivityResult(
        places,
        mode,
        center_id,
        pairs,
        before,
        after,
        after - before if before is not None and after is not None else None,
        sum(pair.before.status == "reachable" for pair in pairs),
        sum(pair.after.status == "reachable" for pair in pairs),
        sum(
            pair.before.status == "reachable" and pair.after.status == "unreachable"
            for pair in pairs
        ),
        sum(pair.before.status == "unbound" or pair.after.status == "unbound" for pair in pairs),
        closed_way_ids,
        graph_version,
    )
