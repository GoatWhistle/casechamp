from datetime import UTC, datetime

from app.domain.normative.library.facts import LibraryFacts
from app.domain.normative.model import AccessRow, Criterion, Facility

INSTANT = datetime(2026, 11, 12, 12, tzinfo=UTC)


def criterion() -> Criterion:
    return Criterion(
        "N07",
        "library",
        "178",
        "18",
        "https://example.org/law",
        "2023-02-08",
        60,
        "minutes",
        "car",
        "Region",
        "conditional",
        "unconfirmed",
    )


def facts() -> LibraryFacts:
    return LibraryFacts(
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
        municipality_type="municipal_okrug",
        municipality_code="37502000",
        planning_scope=True,
        population_verified=True,
        population=100,
        population_reference="population-2026",
        origin_reference_verified=True,
        origin_latitude=55,
        origin_longitude=65,
        routing_node=0,
        approach_metres=0,
        measurement_verified=True,
        measurement_graph_revision="network",
        transport_method_verified=True,
        transport_mode="car",
        eligible_facility_ids=("library",),
        eligible_inventory_complete=True,
        service_eligible=True,
        service_active=True,
    )


def row() -> AccessRow:
    return AccessRow(
        "origin",
        "Place",
        999,
        55,
        65,
        "library",
        30,
        0,
        "within",
        routing_node=0,
        approach_metres=0,
    )


def facility() -> Facility:
    return Facility(
        "library",
        "library",
        "Library",
        "Address",
        "https://example.org/catalog",
        "2026-11-10",
        55,
        65,
        "https://example.org/entrance",
        "verified_entrance",
    )
