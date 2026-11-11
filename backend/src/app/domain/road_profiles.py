from dataclasses import dataclass

SPEED_KMH = {
    "motorway": 90.0,
    "trunk": 65.0,
    "primary": 60.0,
    "secondary": 55.0,
    "tertiary": 50.0,
    "unclassified": 40.0,
    "road": 35.0,
    "residential": 25.0,
    "living_street": 15.0,
    "track": 20.0,
    "service": 15.0,
}
UNPAVED = frozenset(
    {
        "unpaved",
        "gravel",
        "dirt",
        "ground",
        "earth",
        "sand",
        "grass",
        "compacted",
        "fine_gravel",
        "mud",
    }
)
CAPACITY_PER_LANE_PCU_H = 1800.0
UNPAVED_FACTOR = 0.7


@dataclass(frozen=True)
class LaneProfile:
    total: int
    forward: int
    backward: int
    effective: int
    basis: str
    shared: bool = False


def validate_lane_counts(total: int | None, forward: int | None, backward: int | None) -> None:
    for index, value in enumerate([total, forward, backward]):
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
            or (index == 0 and value == 0)
        ):
            raise ValueError(
                "Total lanes must be positive; directional lanes must be nonnegative integers"
            )


def canonical_oneway(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    return {
        "yes": "forward",
        "true": "forward",
        "1": "forward",
        "-1": "reverse",
        "no": "bidirectional",
        "false": "bidirectional",
        "0": "bidirectional",
        "": "unknown",
    }.get(normalized, normalized)


def lane_profile(
    total: int | None, forward: int | None, backward: int | None, oneway: str | None
) -> LaneProfile:
    validate_lane_counts(total, forward, backward)
    if total is not None and any(
        value is not None and value > total for value in [forward, backward]
    ):
        raise ValueError("Directional lanes exceed total lanes")
    one = canonical_oneway(oneway)
    if one not in {"forward", "reverse", "bidirectional", "unknown"}:
        raise ValueError("Unsupported one-way operating mode")
    if one in {"forward", "reverse"}:
        selected, prohibited = (backward, forward) if one == "reverse" else (forward, backward)
        if prohibited not in {None, 0}:
            raise ValueError("One-way road contains prohibited directional lanes")
        if selected == 0:
            raise ValueError("Allowed one-way direction needs positive lanes")
        effective = selected or total or 1
        basis = "osm" if selected is not None or total is not None else "narrow_unknown_lanes_v1"
        return LaneProfile(
            total or effective,
            0 if one == "reverse" else effective,
            effective if one == "reverse" else 0,
            effective,
            basis,
        )
    if forward == 0 or backward == 0:
        raise ValueError("Two-way directional zero lanes are unresolved")
    if total == 1:
        if forward is not None and backward is not None:
            raise ValueError("One physical lane cannot contain two dedicated directional lanes")
        return LaneProfile(1, 1, 1, 1, "osm_shared_single_lane_v1", True)
    if forward is not None and backward is not None:
        if total is not None and forward + backward > total:
            raise ValueError("Directional lane sum exceeds total lanes")
        return LaneProfile(
            total or forward + backward, forward, backward, min(forward, backward), "osm"
        )
    if forward is not None or backward is not None:
        supplied = forward if forward is not None else backward
        assert supplied is not None
        other = total - supplied if total is not None else 1
        if other <= 0:
            raise ValueError("Two-way road needs a positive remaining directional lane count")
        f, b = (supplied, other) if forward is not None else (other, supplied)
        return LaneProfile(
            total or f + b,
            f,
            b,
            min(f, b),
            "osm_total_remainder_v1" if total else "osm_partial_narrow_unknown_lanes_v1",
        )
    if total is not None:
        effective = total // 2
        return LaneProfile(total, effective, effective, effective, "osm_balanced_representative_v1")
    return LaneProfile(2, 1, 1, 1, "narrow_unknown_lanes_v1")
