from app.domain.normative.medical.facts import MedicalFacts
from app.domain.normative.model import AccessRow, Criterion, Facility


def criterion(service: str = "emergency_cardiology") -> Criterion:
    return Criterion(
        "N01" if service == "emergency_cardiology" else "N02",
        service,
        "132n",
        "2",
        "https://example.org/132n",
        "2016-02-27",
        60 if service == "emergency_cardiology" else 120,
        "minutes",
        "car",
        "Region",
        "placement",
        "unconfirmed",
    )


def facts(service: str = "emergency_cardiology") -> MedicalFacts:
    return MedicalFacts(
        service=service,
        origin_id="origin",
        source_url="https://example.org/evidence",
        observed_at="2026-11-10",
        valid_from="2026-11-01",
        valid_until="2026-11-30",
        facts_verified=True,
        legal_currentness_verified=True,
        normative_source_url=criterion(service).source_url,
        legal_edition_date=criterion(service).edition_date,
        jurisdiction_verified=True,
        territory="Region",
        planning_scope=True,
        population_verified=True,
        population=100,
        population_reference="adult-population-2026",
        population_group="adults",
        origin_reference_verified=True,
        origin_latitude=55,
        origin_longitude=65,
        routing_node=0,
        approach_metres=0,
        measurement_verified=True,
        measurement_graph_revision="network",
        transport_method_verified=True,
        transport_mode="car",
        eligible_facility_ids=("clinic",),
        eligible_inventory_complete=True,
        service_eligible=True,
        service_active=True,
        ownership_scope_verified=True,
        ownership_applicable=True,
        facility_form_verified=True,
        adult_profile_verified=True,
        catchment_verified=True,
        catchment_source_url="https://example.org/catchments",
        regional_adjustment_verified=True,
        regional_adjustment_source_url="https://example.org/adjustment",
        threshold_minutes=criterion(service).threshold,
    )


def row() -> AccessRow:
    return AccessRow(
        "origin",
        "Place",
        999,
        55,
        65,
        "clinic",
        30,
        0,
        "within",
        routing_node=0,
        approach_metres=0,
    )


def facility(service: str = "emergency_cardiology") -> Facility:
    return Facility(
        "clinic",
        service,
        "Clinic",
        "Address",
        "https://example.org/catalog",
        "2026-11-10",
        55,
        65,
        "https://example.org/entrance",
        "verified_entrance",
    )
