from dataclasses import asdict

from app.usecase.transit_queries import TransitPlan


def transit_brief(plan: TransitPlan) -> dict[str, object]:
    result = asdict(plan)
    journey = plan.result.journey
    used = {identifier for leg in journey.legs for identifier in (leg.source, leg.target)} if journey else set()
    walks = {(leg.source, leg.target) for leg in journey.legs if leg.mode == 'walk'} if journey else set()
    result['coverage']['stop_count'] = len(plan.coverage.stops)
    result['coverage']['stops'] = [asdict(stop) for stop in plan.coverage.stops if stop.id in used]
    result['result']['walking_links'] = [asdict(link) for link in plan.result.walking_links if (link.source, link.target) in walks]
    return result
