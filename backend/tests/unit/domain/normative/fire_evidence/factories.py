from app.domain.normative.fire import FireProfile
from app.domain.normative.fire_evidence.facts import FireFacts
from app.domain.normative.model import AccessRow, Criterion, Facility


def criterion() -> Criterion:
    return Criterion(
        "N03",
        "fire",
        "123fz",
        "76",
        "https://example.org/law",
        "2022-07-14",
        10,
        "minutes",
        "emergency_response",
        "Region",
        "placement",
        "unconfirmed",
    )


def profile() -> FireProfile:
    return FireProfile(60, "Verified adverse-conditions control profile")


def facts() -> FireFacts:
    return FireFacts(
        origin_id="origin",
        source_url="https://example.org/evidence",
        observed_at="2026-11-10",
        valid_from="2026-11-01",
        valid_until="2026-11-30",
        facts_verified=True,
        legal_currentness_verified=True,
        normative_source_url=criterion().source_url,
        legal_edition_date=criterion().edition_date,
        jurisdiction_verified=True,
        territory="Region",
        planning_scope=True,
        population_verified=True,
        population=100,
        population_reference="measured-objects-2026",
        population_scope="measured_objects",
        population_partition_verified=True,
        origin_reference_verified=True,
        origin_latitude=55,
        origin_longitude=65,
        routing_node=0,
        approach_metres=0,
        measurement_verified=True,
        measurement_graph_revision="network",
        transport_method_verified=True,
        transport_mode="emergency_response",
        eligible_facility_ids=("depot",),
        eligible_inventory_complete=True,
        service_eligible=True,
        service_active=True,
        settlement_type_verified=True,
        settlement_type="urban",
        speed_verified=True,
        speed_kmh=profile().speed_kmh,
        speed_source_url="https://example.org/speed",
        profile_assumption=profile().assumption,
        adverse_conditions_verified=True,
        vehicle_access_verified=True,
        directionality_verified=True,
        operational_readiness_verified=True,
        destination_objects_verified=True,
        measurement_definition_verified=True,
        measurement_definition="depot_to_object_travel",
        method_source_url="https://example.org/method",
        method_currentness_verified=True,
        method_edition_date="2011-02-01",
    )


def row() -> AccessRow:
    return AccessRow(
        "origin", "Place", 999, 55, 65, "depot", 9, 0, "within", routing_node=0, approach_metres=0
    )


def facility() -> Facility:
    return Facility(
        "depot",
        "fire",
        "Depot",
        "Address",
        "https://example.org/catalog",
        "2026-11-10",
        55,
        65,
        "https://example.org/exit",
        "verified_fire_exit",
    )
