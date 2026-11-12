import json
from unittest.mock import Mock

import pytest
from pydantic import TypeAdapter, ValidationError
from pydantic_ai import ModelRetry
from tests.unit.usecase.test_atlas_usecases import FakeAtlas

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.atlas_requests import AtlasPresentation, RoadPresentation
from app.adapter.chat.map_tools import MapTools
from app.domain.errors import DataUnavailable
from app.domain.transport import NetworkMode, Season
from app.usecase.chat import ChatContext
from app.usecase.regions import RegionQueries
from app.usecase.road_geometry import RoadGeometry


def context() -> Mock:
    return Mock(deps=ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen")))


def test_ranked_section_emits_stored_geometry_without_starting_a_calculation() -> None:
    geometry = RoadGeometry(["Lane"], .167, [[[42., 45.], [42.002, 45.]]])
    roads = Mock(geometry=Mock(return_value=geometry))
    tools = MapTools(RegionQueries(FakeAtlas()), roads=roads)
    ctx = context()
    reply = json.loads(tools.present_atlas(ctx, RoadPresentation("road", [123, 123])))
    roads.geometry.assert_called_once_with([123])
    assert reply == {"action": "focus_road", "road_names": ["Lane"], "length_km": .167}
    assert len(ctx.deps.pending) == 1
    assert ctx.deps.pending[0].type == "map"
    assert ctx.deps.pending[0].map.road == geometry
    assert ctx.deps.pending[0].map.region_ids == ()


def test_resolved_selections_expand_on_the_server() -> None:
    roads = Mock(geometry=Mock(return_value=RoadGeometry([], 1., [[[42., 45.], [43., 45.]]])))
    corridors = Mock(get=Mock(return_value=Mock(way_ids=[123, 456])))
    tools = MapTools(RegionQueries(FakeAtlas()), roads=roads, corridors=corridors)
    tools.present_atlas(context(), RoadPresentation("road", [123], ["selected"]))
    corridors.get.assert_called_once_with("selected")
    roads.geometry.assert_called_once_with([123, 456])


@pytest.mark.parametrize("lines", [[], [[]], [[[42., 45.]]], [[[42., 45.], [float("nan"), 45.]]]])
def test_missing_or_invalid_geometry_never_emits_a_command(lines: list[list[list[float]]]) -> None:
    roads = Mock(geometry=Mock(return_value=RoadGeometry([], 0., lines)))
    tools = MapTools(RegionQueries(FakeAtlas()), roads=roads)
    ctx = context()
    with pytest.raises(ModelRetry, match="geometry"):
        tools.present_atlas(ctx, RoadPresentation("road", [123]))
    assert ctx.deps.pending == []


def test_unknown_way_and_empty_target_are_recoverable_tool_errors() -> None:
    roads = Mock(geometry=Mock(side_effect=DataUnavailable("Geometry is missing")))
    tools = MapTools(RegionQueries(FakeAtlas()), roads=roads)
    ctx = context()
    with pytest.raises(ModelRetry, match="known positive way IDs"):
        tools.present_atlas(ctx, RoadPresentation("road"))
    roads.geometry.assert_not_called()
    with pytest.raises(ModelRetry, match="Geometry is missing"):
        tools.present_atlas(ctx, RoadPresentation("road", [999]))
    assert ctx.deps.pending == []


def test_model_supplies_identifiers_instead_of_geometry() -> None:
    with pytest.raises(ValidationError, match="lines"):
        TypeAdapter(AtlasPresentation).validate_python({
            "kind": "road", "way_ids": [123], "lines": [[[42., 45.], [43., 45.]]],
        })
