# Endpoint road routing

2026-11-11, feat/map-first-ui, base cdb2c2e. No commit/push/remote deployment.
User reports a visible road cannot be found and requests bidirectional search.
Clarified endpoints: Stavropol and Aleksandrovskoye (Stavropol Krai).

Observed original failure: live chat logs twice report resolve_road_corridor unresolved
with Road reference is ambiguous or missing. That tool requires one matched OSM ref
before it searches any path. Endpoint routing was absent. A deterministic regression
at the actual CorridorTools -> RoadCorridors -> CorridorResolver seam failed with
missing resolve_road_route before implementation, then passed across three roads with
different/missing references. One initial fixture had a required params argument for
an optional read parameter; corrected to match the real port.

Implemented resolve_road_route as a separate operation, preserving specific-named-road
resolution. It uses attached settlement nodes in the complete base road CSR, with two
Dijkstra frontiers. Best-path lower-bound termination avoids the invalid first-discovery
intersection stopping rule. Directed graphs use the transpose; the active symmetric
road graph shares the same CSR in both directions. No virtual gaps, air/rail edges,
source changes or automatic scenario submission. Returned corridor can be closed via
the existing tool, with whole-way scope explicitly stated. Missing highway labels no
longer prevent generic endpoint road requests. Alternatives are not silently presented
as a requested named highway. The road skill and capabilities advertise the tool.

Live validation: PYTHONPATH=backend/src backend/.venv/bin/python work/road-route/validate.py
with .env.analytics exported. validation.json stores the actual geometry and version.
Stavropol -> selo Aleksandrovskoye,70ways,refs07K-001/R-216/07K-003,
1.8282827356746836modelhours including0.01601/0.03842km attachments.
109.93382km is the sum of whole selected ways, not exact trip mileage.
1.10327seconds after graph preparation; not a cold-start benchmark.
SciPy's independent unidirectional result matches to1e-7hours.
Graph road-8033092fca2cf5fa, road-capacity-v1. No index-model label in source metadata.

Verification: Ruff pass, mypy217files pass,315unit tests pass,45ClickHouseintegration
pass. Seeded directed/undirected differential tests compare72ODpairs with SciPy;
first-intersection counterexample, disconnected vertices and bounded exploration
on10000nodechain also pass. Five new source/test files checked/formatted separately.
Global ruff format --check is NOT clean:58files initially flagged, including unrelated
pre-existing files. No mass formatting of concurrent work. gitdiffcheck and skillvalidator
pass. No paid LLM calls or browser-submitted calculations.

API8007 restarted only with both scenario/analysis queues idle, same env/settings.
Current PID71467, log/tmp/plexus-road-route-api.log; health passed. Prior saved jobs
preserved. Chrome was inspected read-only to locate the original request and returned
to its initial tab; exact endpoint clarification came from user. No frontend/mobile
changes. Prior appraisal/capacity/chat/map modifications preserved.
