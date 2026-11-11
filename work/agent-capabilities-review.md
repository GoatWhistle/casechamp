# Agent and calculation capability review

Reviewed 2026-11-11 on `feat/map-first-ui`, HEAD
`cdb2c2e1108bde7ff37ab91f9d7907d05de2a897`, including the existing uncommitted work.
User request: «изучи что уже умеет ии агент и что мы умеем считать».
No product code, data, running services or model configuration changed.

## Agent surface

Sources: `backend/src/app/adapter/chat/{gateway,tools,calculation_tools,tool_visibility,
stress_tools,atlas_requests}.py` and the six bundled analyst skills under that directory.

- Starts with `load_skill` and `query_atlas`; skills activate specialized tools per turn.
- Reads region summaries, settlements, source links, provenance, calculation capabilities
  and uniform-time sensitivity. Sorted regional tables support Hansen, population,
  seasonal link count, settlement count and company count.
- Resolves roads by endpoints or highway name, bridge selections, graph nodes and
  local/intercity transport links. Coordinates and road selections come from backend data.
- Calculates road closures, speed/profile changes, new connections, combined rail/air
  and road scenarios, selected-settlement connectivity and candidate road rankings.
- Default selected-road closure combines regional Hansen with national road consequences;
  optional places/traffic adds the separate assumed-load pair experiment.
- Reads saved jobs, compares scenarios in server-generated tables, cancels jobs and
  continues analysis batches. Focuses regions/settlements and draws charts from tool tables.
- Streams prose and artifacts; completed background jobs trigger interpretation from
  saved results. This is an implemented mechanism, not proof of reliable free-text planning.
- Six maintained skills, but up to nine registered public tools with stress enabled:
  the six general interfaces plus `stress_test_roads`, `inspect_road_stress_test` and
  `compare_stress_route`. The six-interface documentation predates those additions.

## Calculations and distinctions

- Regional Hansen discounts 180 market populations by travel time, then weights origins
  by population on a fixed normalization. It includes own-market contribution.
- Road scenarios recompute regional Hansen, affected settlements and accessibility changes.
  New single-link additions have a delta path; closures/full network edits reroute.
- National stress uses road-only routing without the regional model's 72-hour cutoff:
  lost markets, new loss of all external markets, delays, affected residents, regional
  thresholds, nearby connections and actual before/after route geometry and distance.
- Selected groups contain 2–12 settlements, with all pairs or trips to one center.
  Their mean score is based on `100 * 2**(-hours/2)`, distinct from regional Hansen.
- Traffic experiments support 2–4 places and independent representative-direction pairs.
  Defaults are 50% utilization, one hour and 1800 PCU per lane-hour. Up to five disjoint
  detours receive flow, with capacity ratios, queues, delay and unserved demand reported.
  Pairs cannot be summed; this is not regional traffic assignment or observed congestion.
- Conditional economics: supplied passenger/freight flows, route times/distances and rates;
  annual effects, low/base/high scenarios, NPV, BCR and discounted public-benefit payback.
  Saved traffic results support a separate transit-cohort time-cost calculation.
- Offline pipeline additionally computes Harris, cumulative reachable population at
  1/2/4 hours, CA/ARIA remoteness proxies, OECD-like remoteness, district-center access,
  geometric RAI proxy, network efficiency, Gini/Palma/Theil, accessibility poverty and
  seasonal gaps. Sources: `etl/road_capacity/{metrics,aggregate}.py`.
- These additional metrics are not exposed by `query_atlas`/the current regional DTO.
  Saved potential-accessibility and modal-removal comparisons have an API/UI path,
  but no dedicated agent query. Their historical snapshot must not be mixed with current
  road scenario results.
- No GDP/GRP, company revenue or observed demand forecast; no exact timetable routing,
  one-way/frequency service edits, truck restrictions or full dynamic congestion model.
- Lane expansion alone leaves free-flow time unchanged without confirmed flow. Class,
  surface and design speed can change it. Confirmed flow profiles were zero in the
  road-capacity validation; missing lane counts use one lane per direction.

## Evidence checked this session

- Local read-only HTTP check: health OK, 82 regions, 180 markets. API model label
  `hansen-release-20261107`; artifact
  `adeb4170a71a6b9bbb8b5b5fe6de0a627e1e9a83b483e0328a0b172cb2964b29`
  matches `docs/results/road-capacity-validation.json` (`road-capacity-v1`).
  Model label and road-cost version name different aspects of this snapshot.
- 93 focused backend tests passed in 1.11 seconds. From `backend/`:

```sh
.venv/bin/python -m pytest tests/unit/adapter/chat tests/unit/adapter/road_corridor/test_group_connectivity.py tests/unit/adapter/road_corridor/test_connectivity_memory.py tests/unit/adapter/road_corridor/test_connectivity_followup.py tests/unit/domain/test_project_appraisal.py tests/unit/domain/test_connectivity.py tests/unit/domain/test_road_stress.py tests/unit/usecase/test_calculation_tables.py tests/unit/usecase/test_chat_calculation_review.py -q -n 0
```

- Read historical numerical protocols and their scope in `docs/road-stress.md`,
  `docs/traffic-diversion.md`, `docs/economic-appraisal.md`, `docs/road-capacity.md`,
  `docs/indices.md` and `docs/potential-accessibility.md`.
- No paid model call, fresh nationwide calculation, integration suite or browser check
  this session. Tool tests do not establish end-to-end natural-language agent reliability.
- Initial sandbox localhost request was blocked; approved read-only request succeeded.
  A search assumed a nonexistent `metrics.json`; metric definitions were found in Python.

Next if requested: expose existing additional metrics through the unified agent query;
evaluate free-text tool selection on representative user tasks with explicit model-run
authorization. Preserve current services and unrelated working-tree changes.
