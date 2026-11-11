from dataclasses import replace
from uuid import uuid4

from app.adapter.road_graph.data import GraphData
from app.domain.appraisal_inputs import ProjectAssumptions
from app.domain.errors import InvalidQuery
from app.domain.road_economics import MoneyAssumptions
from app.usecase.road_graph import RoadAddition, RoadJob


def locate_addition(data: GraphData, addition: RoadAddition) -> RoadAddition:
    data.load()
    nodes = (addition.source_node, addition.target_node)
    if any(node >= len(data.nodes["lat"]) for node in nodes):
        raise InvalidQuery("Unknown graph node")
    addition = replace(
        addition,
        coordinates=[
            [float(data.nodes["lon"][node]), float(data.nodes["lat"][node])] for node in nodes
        ],
    )
    return addition


def addition_job(
    region_id: str,
    region: str,
    addition: RoadAddition,
    money: MoneyAssumptions | None,
    appraisal: ProjectAssumptions | None,
    version: str,
) -> RoadJob:
    return RoadJob(
        uuid4().hex,
        region_id,
        region,
        "road",
        [],
        "queued",
        0,
        5,
        version,
        addition=addition,
        money_assumptions=money,
        appraisal_assumptions=appraisal,
    )
