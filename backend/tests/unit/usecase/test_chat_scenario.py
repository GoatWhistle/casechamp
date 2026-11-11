from app.usecase.chat_scenario import road_kind


def test_road_kind_names_uniform_changes() -> None:
    assert road_kind([0, 0]) == "closure"
    assert road_kind([1.5, 2]) == "speed"
    assert road_kind([0.5]) == "slowdown"


def test_road_kind_falls_back_for_mixed_or_empty_changes() -> None:
    assert road_kind([0, 1.5]) == "roads"
    assert road_kind([1]) == "roads"
    assert road_kind([]) == "roads"
