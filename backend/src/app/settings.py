from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    chat_enabled: bool = False
    graph_dir: Path | None = None
    clickhouse_url: str = "http://127.0.0.1:18123"
    clickhouse_user: str = "plexus"
    clickhouse_password: str = ""
    road_workers: int = 1
    traffic_workers: int = 32
    traffic_geography: Path | None = None
    municipal_dataset: Path = (
        Path(__file__).resolve().parents[3] / "datasets/municipal-indices"
    )
    contextual_water: Path = (
        Path(__file__).resolve().parents[3] / "datasets/contextual-water/contextual-water.json"
    )
    contextual_boundaries: Path = (
        Path(__file__).resolve().parents[3]
        / "datasets/display-context-boundaries/contextual-regions.json"
    )
    normative_archive: Path = (
        Path(__file__).resolve().parents[3] / "docs/results/normative-live-index-coverage.json"
    )


def load_settings(env: Mapping[str, str]) -> Settings:
    return Settings(
        graph_dir=Path(env["GRAPH_DIR"]) if env.get("GRAPH_DIR") else None,
        chat_enabled=env.get("CHAT_ENABLED", "false").lower() == "true",
        clickhouse_url=env.get("CLICKHOUSE_URL") or "http://127.0.0.1:18123",
        clickhouse_user=env.get("CLICKHOUSE_USER", "plexus"),
        clickhouse_password=env.get("CLICKHOUSE_PASSWORD", ""),
        road_workers=int(env.get("ROAD_WORKERS", "1")),
        traffic_workers=min(32, max(1, int(env.get("TRAFFIC_WORKERS", "32")))),
        traffic_geography=Path(env["TRAFFIC_GEOGRAPHY"]) if env.get("TRAFFIC_GEOGRAPHY") else None,
        municipal_dataset=Path(env["MUNICIPAL_DATASET"])
        if env.get("MUNICIPAL_DATASET")
        else Path(__file__).resolve().parents[3] / "datasets/municipal-indices",
        contextual_water=Path(env["DISPLAY_CONTEXT_WATER"])
        if env.get("DISPLAY_CONTEXT_WATER")
        else Path(__file__).resolve().parents[3]
        / "datasets/contextual-water/contextual-water.json",
        contextual_boundaries=Path(env["DISPLAY_CONTEXT_BOUNDARIES"])
        if env.get("DISPLAY_CONTEXT_BOUNDARIES")
        else Path(__file__).resolve().parents[3]
        / "datasets/display-context-boundaries/contextual-regions.json",
        normative_archive=Path(env["NORMATIVE_ARCHIVE"])
        if env.get("NORMATIVE_ARCHIVE")
        else Path(__file__).resolve().parents[3]
        / "docs/results/normative-live-index-coverage.json",
    )
