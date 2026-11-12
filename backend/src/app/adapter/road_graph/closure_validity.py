from dataclasses import replace

from app.adapter.road_graph.attachment_audit import AttachmentAudit, SettlementAttachmentConflict
from app.usecase.road_graph import RoadJob
from app.usecase.road_stress import StressJob


def road_job_view(job: RoadJob, audit: AttachmentAudit) -> RoadJob:
    if job.status == "completed":
        try:
            audit.validate([c.way_id for c in job.changes if c.speed_factor == 0])
        except SettlementAttachmentConflict as error:
            return replace(
                job, status="failed", result=None, appraisal_result=None, error=error.code
            )
    return job


def stress_job_view(job: StressJob, audit: AttachmentAudit) -> StressJob:
    if job.status == "completed":
        try:
            audit.validate(job.way_ids)
        except SettlementAttachmentConflict as error:
            return replace(
                job,
                status="failed",
                stage="failed",
                regions=[],
                newly_isolated_points=0,
                error=error.code,
            )
    return job
