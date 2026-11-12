from app.domain.errors import DataUnavailable, InvalidQuery
from app.domain.normative.fire import FireProfile
from app.domain.normative.model import Criterion
from app.usecase.normative.interface import NormativeFireRouting, NormativeRouting


def routing_for(
    criterion: Criterion,
    road: NormativeRouting | None,
    walking: NormativeRouting | None,
    fire: NormativeFireRouting | None = None,
    profile: FireProfile | None = None,
) -> NormativeRouting:
    if criterion.mode == "emergency_response" and criterion.service == "fire":
        if fire is None:
            raise DataUnavailable("Fire travel routing is not configured")
        if profile is None:
            raise InvalidQuery("Specify a fire travel speed and its assumption; no default is used")
        return fire.with_profile(profile)
    if profile is not None:
        raise InvalidQuery("Fire travel parameters only apply to N03")
    if criterion.mode == "walk" and criterion.unit == "metres":
        if walking is None:
            raise DataUnavailable("Pedestrian routing is not configured")
        return walking
    if (
        criterion.mode == "car"
        or (criterion.mode == "territory_specific" and criterion.service == "library")
    ) and criterion.unit == "minutes":
        if road is None:
            raise DataUnavailable("Road routing is not configured")
        return road
    raise DataUnavailable("This criterion requires a dedicated transport model")
