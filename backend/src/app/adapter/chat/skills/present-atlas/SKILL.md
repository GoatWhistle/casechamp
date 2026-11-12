---
name: present-atlas
description: Present rankings, charts or map focus for regions, settlements and road graph sections using verified data.
---

# Present atlas evidence

Use `query_atlas(kind=regions, metric=...)` for rankings/comparisons so the UI receives the actual table.
Only use supported metrics, and preserve the requested sort direction. For a chart,
call `present_atlas(kind=chart)` with a returned table_id and numeric column (x=name for regions).
Do not duplicate the whole table in prose or invent values to make a chart.
Lead with the useful comparison and explain the meaning using the relevant domain skill.

Use `present_atlas(kind=map)` when the user asks to show, highlight, focus, zoom or reset.
For a group, pass all region IDs in one focus action to avoid successive flights.
For a city, village or other settlement, resolve its exact ID with `query_atlas(kind=places)`
or `query_atlas(kind=settlements)`, then use `present_atlas(kind=settlement, settlement_id=...)`.
Use region context to distinguish namesakes; ask only if multiple choices remain.
The server reads coordinates from storage. Do not supply or invent coordinates.
Settlement focus zooms to the point, labels it and selects its parent region.
For a road or graph section, use `present_atlas(kind=road, way_ids=[...])` with exact
IDs from the ranking, viewport or selected map context. For a resolved corridor or
bridge, pass `selection_ids=[...]` from `find_transport` instead. The server loads
the geometry, highlights the section and fits the camera to its bounds. Showing a
road requires no new scenario calculation. For “show that lane”, reuse the ranked
candidate's way_id so the camera shows the checked section, not the whole street.
If its ID is missing from history, read the saved analysis with `manage_calculation`
or resolve the requested road with `find_transport`; distinguish namesakes by place.
Coordinates come from storage. Claim a map action only after its tool succeeds.

Tables, charts, calculation cards and road-analysis rankings appear in chat. Describe
the main conclusion rather than directing users to another page. Pending calculations
have no final result. Put substantive uncertainty in the answer; optional source URLs
and technical scope can use separate Sources: and Scope: paragraphs for folded details.
Use Markdown and dollar-delimited LaTeX when useful. Never output raw JSON as prose.
