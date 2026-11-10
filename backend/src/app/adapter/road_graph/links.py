from typing import Any

from app.domain.errors import InvalidQuery
from app.domain.settlement_names import normalized_place, settlement_name
from app.usecase.transport_links import LinkChange, TransportLink

TRANSFER_HOURS = {"rail": 1.0, "air": 2.5}


def touches(link: LinkChange, a: str, b: str) -> bool:
    if link.target == "*":
        return link.source in (a, b)
    return {a, b} == {link.source, link.target}


def canonical_links(links: list[LinkChange], cities: list[str]) -> list[LinkChange]:
    names = {settlement_name(city): city for city in cities}
    result = []
    for link in links:
        if link.network == "local":
            result.append(link)
            continue
        ends = []
        for value in (link.source, link.target):
            if value == "*":
                ends.append(value)
            elif settlement_name(value) in names:
                ends.append(names[settlement_name(value)])
            else:
                raise InvalidQuery(
                    f"Intercity links connect the 180 market cities; unknown city: {value}"
                )
        result.append(LinkChange(link.action, link.network, link.mode, ends[0], ends[1], link.hours))
    return result


def apply_trunk(rows: list[tuple[Any, ...]], links: list[LinkChange]) -> list[tuple[Any, ...]]:
    changes = [link for link in links if link.network == "intercity"]
    kept = [
        row for row in rows
        if not any(
            link.action == "remove" and link.mode == row[2] and touches(link, row[0], row[1])
            for link in changes
        )
    ]
    for link in changes:
        if link.action == "add":
            kept += [
                (link.source, link.target, link.mode, link.hours),
                (link.target, link.source, link.mode, link.hours),
            ]
    return kept


def apply_manual(rows: list[tuple[Any, ...]], links: list[LinkChange]) -> list[tuple[Any, ...]]:
    changes = [link for link in links if link.network == "local"]
    kept = [
        row for row in rows
        if not any(
            link.action == "remove" and link.mode == row[3] and touches(link, row[0], row[1])
            for link in changes
        )
    ]
    for link in changes:
        if link.action == "add":
            kept += [
                (link.source, link.target, link.hours, link.mode),
                (link.target, link.source, link.hours, link.mode),
            ]
    return kept


def missing_removals(
    trunk: list[tuple[Any, ...]], manual: list[tuple[Any, ...]], links: list[LinkChange]
) -> list[LinkChange]:
    missing = []
    for link in links:
        if link.action != "remove":
            continue
        rows = trunk if link.network == "intercity" else [(r[0], r[1], r[3]) for r in manual]
        if not any(link.mode == row[2] and touches(link, row[0], row[1]) for row in rows):
            missing.append(link)
    return missing


def intercity_links(
    rows: list[tuple[Any, ...]], place: str, mode: str | None
) -> list[TransportLink]:
    wanted = settlement_name(place)
    seen: dict[tuple[str, str, str], TransportLink] = {}
    for a, b, kind, hours in rows:
        if mode and kind != mode:
            continue
        if wanted not in (settlement_name(str(a)), settlement_name(str(b))):
            continue
        key = (min(a, b), max(a, b), kind)
        if key not in seen or hours < seen[key].hours:
            seen[key] = TransportLink("intercity", kind, a, a, b, b, float(hours))
    return sorted(seen.values(), key=lambda link: (link.mode, link.hours))[:60]


def local_links(
    rows: list[tuple[Any, ...]], place: str, mode: str | None
) -> list[TransportLink]:
    wanted = normalized_place(place)
    result = []
    for a, a_name, b, b_name, kind, hours, region in rows:
        names = [normalized_place(str(a_name or "")), normalized_place(str(b_name or ""))]
        region_name = normalized_place(str(region or ""))
        if mode and kind != mode:
            continue
        if not (
            wanted in (str(a), str(b)) or wanted == region_name
            or any(settlement_name(wanted) == settlement_name(n) for n in names)
        ):
            continue
        result.append(TransportLink(
            "local", kind, str(a), str(a_name or a), str(b), str(b_name or b), float(hours),
            str(region) if region else None,
        ))
    return result[:80]
