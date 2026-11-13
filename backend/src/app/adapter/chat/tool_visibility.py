from pydantic_ai import RunContext, ToolDefinition

from app.adapter.chat.artifacts import ChatRun

TRANSPORT_SKILLS = frozenset({
    "road-scenarios", "rail-air-scenarios", "economic-assessment", "settlement-connectivity",
})


async def analyst_tools(
    ctx: RunContext[ChatRun], definitions: list[ToolDefinition]
) -> list[ToolDefinition]:
    enabled = {"load_skill", "query_atlas"}
    if ctx.deps.title is None:
        enabled.add("name_chat")
    if ctx.deps.loaded_skills & TRANSPORT_SKILLS:
        enabled.update({"municipal_analysis", "find_transport", "calculate_scenario", "manage_calculation", "stress_test_roads", "inspect_road_stress_test", "compare_stress_route"})
    if "present-atlas" in ctx.deps.loaded_skills:
        enabled.add("present_atlas")
    return [definition for definition in definitions if definition.name in enabled]
