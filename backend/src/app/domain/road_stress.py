from math import isfinite


def compare_market_times(
    before: list[float], after: list[float], markets: list[str], own_market: str
) -> tuple[int, bool, float, str]:
    if len(before) != len(after) or len(before) != len(markets):
        raise ValueError("Market vectors must match")
    lost = 0
    reachable_before = reachable_after = 0
    worst_delay = 0.0
    worst_market = ""
    for a, b, market in zip(before, after, markets, strict=True):
        if market == own_market:
            continue
        reachable_before += int(isfinite(a))
        reachable_after += int(isfinite(b))
        if isfinite(a) and not isfinite(b):
            lost += 1
            if lost == 1:
                worst_market = market
        elif isfinite(a) and isfinite(b):
            if b < a - 1e-6:
                raise ValueError("A closure cannot shorten a route")
            delay = max(0.0, (b - a) * 60)
            if delay > worst_delay:
                worst_delay = delay
                if not lost:
                    worst_market = market
    return lost, reachable_before > 0 and reachable_after == 0, worst_delay, worst_market
