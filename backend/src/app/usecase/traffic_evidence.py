import json
from dataclasses import replace

from app.usecase.traffic import TrafficJob


def public_traffic_job(job: TrafficJob) -> TrafficJob:
    evidence = json.loads(job.provenance)
    if "verified_observations" not in evidence:
        return job
    evidence.pop("verified_observations")
    return replace(job, provenance=json.dumps(evidence, ensure_ascii=False))
