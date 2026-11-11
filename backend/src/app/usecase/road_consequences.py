from dataclasses import dataclass


@dataclass(frozen=True)
class DelayExposure:
    threshold_minutes: int
    settlements: int
    residents: int


@dataclass(frozen=True)
class NearbyAccessChange:
    threshold_hours: float
    changed_connections: int
    lost_connections: int
    comparable_connections: int
    mean_before_minutes: float | None
    mean_after_minutes: float | None
    mean_added_minutes: float | None
    connections_crossing_threshold: int
    settlements_crossing_threshold: int
    residents_crossing_threshold: int


@dataclass(frozen=True)
class DestinationConsequence:
    destination: str
    settlements: int
    exposed_residents: int
    lost_connections: int
    residents_losing_connection: int
    nearby_exposed_residents: int
    comparable_connections: int
    mean_before_minutes: float | None
    mean_after_minutes: float | None


@dataclass(frozen=True)
class ConnectionConsequence:
    origin_id: str
    origin: str
    residents: int
    destination: str
    before_minutes: float
    after_minutes: float | None
    added_minutes: float | None


@dataclass(frozen=True)
class RegionalConsequences:
    region: str
    lost_connections: int
    settlements_losing_connections: int
    residents_losing_connections: int
    delay_exposure: list[DelayExposure]
    nearby_access: NearbyAccessChange
    destinations: list[DestinationConsequence]
    examples: list[ConnectionConsequence]
    method: str = "saved_road_closure_consequences_v1"
    scope: str = "recorded_changed_settlement_market_connections_in_selected_region"
    minimum_recorded_delay_minutes: float = 1.0
