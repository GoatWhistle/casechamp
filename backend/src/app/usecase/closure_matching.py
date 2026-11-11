from app.usecase.road_records import RoadChange, RoadJob


def matching_closure_jobs(jobs: list[RoadJob], way_ids: list[int], version: str) -> list[RoadJob]:
    ways = set(way_ids)
    matches: dict[str, RoadJob] = {}
    for job in jobs:
        if (
            job.version == version
            and job.scenario == "road"
            and not job.links
            and not job.addition
            and job.changes
            and {c.way_id for c in job.changes} == ways
            and all(c == RoadChange(c.way_id, 0) for c in job.changes)
        ):
            previous = matches.get(job.region_id)
            if previous is None or previous.status != "completed":
                matches[job.region_id] = job
    return list(matches.values())
