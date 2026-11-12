from dataclasses import replace

from app.domain.errors import DataUnavailable
from app.domain.normative.fire_destination import FireDestination
from app.domain.normative.model import AccessRow, Origin
from app.usecase.normative.interface import NormativeOriginAttachment


def object_origins(
    destinations: list[FireDestination], attachment: NormativeOriginAttachment | None, revision: str
) -> list[Origin]:
    if not destinations:
        raise DataUnavailable("No sourced fire destination objects have been imported")
    if len({d.id for d in destinations}) != len(destinations):
        raise DataUnavailable("Fire destination identifiers are duplicated")
    if attachment is None:
        raise DataUnavailable("Fire destination attachment is not configured")
    origins = [
        Origin(d.id, d.name + ", " + d.address, None, None, None, d.latitude, d.longitude)
        for d in destinations
    ]
    return attachment.attach(origins, revision)


def describe_objects(rows: list[AccessRow], destinations: list[FireDestination]) -> list[AccessRow]:
    if not destinations:
        return rows
    source = {d.id: d for d in destinations}
    return [
        replace(
            row,
            origin_source_url=source[row.id].source_url,
            origin_observed_at=source[row.id].observed_at,
            origin_source_sha256=source[row.id].source_sha256,
            origin_reference_status=source[row.id].reference_status,
        )
        for row in rows
    ]
