import json
from dataclasses import replace
from unittest.mock import Mock, patch

import pytest
from pydantic import TypeAdapter, ValidationError
from pydantic_ai import ModelRetry
from tests.unit.usecase.test_atlas_usecases import FakeAtlas

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.atlas_requests import AtlasPresentation, SettlementPresentation
from app.adapter.chat.map_tools import MapTools
from app.domain.transport import NetworkMode, Season
from app.usecase.chat import ChatContext
from app.usecase.dto import PointRecord
from app.usecase.regions import RegionQueries
from app.usecase.settlements import SettlementQueries


class FocusAtlas(FakeAtlas):
    def points(self) -> dict[str, PointRecord]:
        return {
            "one": PointRecord("one", "Same name", "01000000", 45., 42., 0., 0.),
            "two": PointRecord("two", "Same name", "02000000", 56., 63., 0., 0.),
        }


def test_focus_resolves_the_requested_id_and_emits_stored_coordinates() -> None:
    atlas = FocusAtlas()
    tools = MapTools(RegionQueries(atlas), SettlementQueries(atlas))
    ctx = Mock(deps=ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen")))
    result = json.loads(tools.present_atlas(ctx, SettlementPresentation("settlement", "two")))
    assert result["action"] == "focus_settlement"
    assert result["region_ids"] == ["02000000"]
    assert result["settlement"]["longitude"] == 63
    assert result["settlement"]["latitude"] == 56
    assert ctx.deps.pending[0].map.settlement.id == "two"


def test_unknown_or_invalid_location_never_emits_a_map_event() -> None:
    atlas = FocusAtlas()
    tools = MapTools(RegionQueries(atlas), SettlementQueries(atlas))
    ctx = Mock(deps=ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen")))
    with pytest.raises(ModelRetry, match="coordinates are unavailable"):
        tools.present_atlas(ctx, SettlementPresentation("settlement", "unknown"))
    with (
        patch.object(atlas, "point", return_value=replace(atlas.points()["one"], lat=float("nan"))),
        pytest.raises(ModelRetry, match="invalid map coordinates"),
    ):
        tools.present_atlas(ctx, SettlementPresentation("settlement", "one"))
    assert ctx.deps.pending == []


def test_model_cannot_supply_its_own_coordinates() -> None:
    with pytest.raises(ValidationError, match="longitude"):
        TypeAdapter(AtlasPresentation).validate_python({
            "kind": "settlement", "settlement_id": "one", "longitude": 42., "latitude": 45.,
        })
