# Bridge selection and combined closure

Implemented 2026-11-10 on feat/map-first-ui. Current HEAD observed at closeout:
46e7b1ab2c23417e070a64306a176cbcce419fc6. Other sessions are committing unrelated work;
this task has not itself committed or pushed.

The original failure is documented in ../bridge-chat-failure.md. The follow-up
request was to solve actual bridge identification, beyond reporting that it is
unsupported. Added find_road_bridges and close_road_bridges, backed by existing
ClickHouse is_bridge attributes, full road_lines geometry and the real road worker.

Selected from the active graph, without production hardcoded bridge IDs:

- Direct Saratov–Engels: way203336910, named Саратовский мост, 2.802 km in the graph.
- Pristannoe main river span: ways27262951 and122013785, СКАД / А-298. Two parallel
  carriageways, total stored way length4.666 km. This is not the physical bridge length.
- Combined closure: all three way IDs at speed_factor0, one job for Saratov region63000000.

The Pristannoe correspondence follows location, bridge tags, A-298 reference and
parallel span geometry. The Ministry of Transport describes a main river bridge
and separate channel bridges in this crossing:
https://www.mintrans.gov.ru/eye/press-center/news/3858 . The selected scenario closes
the main river span's two decks, not every channel bridge or the entire bypass.
Do not represent this as verified current operating restrictions or actual traffic.

Evidence:

- acceptance.json: actual tool selection, graph revision, combined submission and UI event.
- replay.py: manual replay using real ClickHouse reads and the local API worker for submission.
  Re-running starts/reuses a real job; it is not an offline unit test.
- job.json: last observed state of job a65a94bb2d9f43afbdd94a546a7157c8. Pending, no effect claimed.
- chat-1440.png and chat-1920.png: isolated browser replay of the actual tool event,
  with live job polling. No paid model call or synthetic calculation result.

Validation: Ruff/mypy pass,195 backend unit tests pass, frontend verify passes415
tests and build. Integration suite:41 pass,2 fail in concurrently developed
test_accessibility_storage.py (storage unavailable/HTTP503); bridge-selection
integration passes, including a separate rerun after distance-to-polyline refinement.
Browser has no page errors, displays a single three-way closure card and both
bridge overlays. Initial overlay wait timed out while map initialization was slow;
the1920 capture shows both overlays,1440 was captured before base tiles appeared.

Runtime: API8001 PID50312, persistent exec session54927, /tmp/plexus-local-api.log.
New tools are loaded. A later distance-to-polyline/80m search-margin refinement is
on disk and tested but requires the next idle API restart; do not interrupt this
running job just to reload it. Current selected ways are identical with either version.

Next: let the combined full-network job finish, record actual before/after or failure,
then reload API when idle to include the distance refinement. Selection is heuristic
for generic OSM bridges, with explicit candidate ambiguity; cross-region calculations
cover the search-settlement regions, not every region potentially affected nationwide.
