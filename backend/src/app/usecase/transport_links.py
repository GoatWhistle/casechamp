from dataclasses import dataclass
from math import isfinite

from app.domain.errors import InvalidQuery


@dataclass(frozen=True)
class LinkChange:
    action: str
    network: str
    mode: str
    source: str
    target: str
    hours: float | None = None


@dataclass(frozen=True)
class TransportLink:
    network: str
    mode: str
    source: str
    source_name: str
    target: str
    target_name: str
    hours: float
    region: str | None = None


INTERCITY_MODES = frozenset({"rail", "air"})
LOCAL_MODES = frozenset({"air", "river", "ferry", "winter_road", "ice_crossing", "pontoon_bridge"})


def validate_links(links: list[LinkChange]) -> None:
    for link in links:
        modes = INTERCITY_MODES if link.network == "intercity" else LOCAL_MODES
        if link.action not in {"add", "remove"} or link.network not in {"intercity", "local"}:
            raise InvalidQuery("Действие связи: add или remove; сеть: intercity или local")
        if link.mode not in modes:
            raise InvalidQuery(f"Вид связи для сети {link.network}: {', '.join(sorted(modes))}")
        if not link.source.strip() or not link.target.strip() or link.source == link.target:
            raise InvalidQuery("Укажите два разных конца связи")
        if link.action == "add" and (
            link.target == "*" or link.hours is None or not isfinite(link.hours)
            or not 0 < link.hours <= 72
        ):
            raise InvalidQuery("Новой связи нужны конкретный второй конец и время в пределах (0, 72] ч")
