# Passport from the organizer template

Task date: 2026-11-10. Branch: feat/map-first-ui, HEAD c82ab1e.
Output: root `Паспорт проекта Plexus.docx`. Original template remains unchanged.
Also delivered `Паспорт проекта Plexus.md` at the user's explicit request, converted
from the final DOCX. The nine sections, content and blank fields match; hyperlinks
are preserved and existing local documentation paths are clickable relative links.

Follow-up: added concrete descriptions of Clean Architecture, the tool-using AI agent
and graph size to both formats. Graph counts are 6,990,556 nodes and 17,393,384 directed
edges from the complete migration equality check on 2026-11-10, not the larger staging
graph that has not replaced the runtime. Architecture was checked against main.py,
usecase/interface.py, usecase/chat.py and domain/usecase imports. Agent behavior was
checked against adapter/chat/gateway.py, tools.py and calculation_tools.py. No new model
request was run. Latest render: /private/tmp/plexus-passport/architecture-final.

The user explicitly prohibits future plans. Removed the roadmap and renumbered expert
questions. Team, representative and participant roles remain blank under prior user
instructions. Deployment URL remains blank at the user's request. Coursework uses the
six subjects supplied by the user; completion/enrollment status is not invented.
The user confirms team testing through the interface and no external user/expert testing.

Evidence used:
- docs/road-analysis.md and docs/results/road-analysis-validation.json: four completed
  road calculations on 2026-11-10, one OSM way in each of two regions, fixed population
  and normalization; exact calculation times rounded to 340–367 seconds.
- docs/clickhouse.md, work/clickhouse-migration/live-verification.json and current
  ClickHouseAtlasRepository: runtime reads atlas_indices, not atlas_exported_indices.
  Do not confuse the older five-scenario national export with the active graph snapshot.
- docs/indices.md and current road_graph/delta.py: Hansen formula, two-hour half-life,
  population weighting; current graph snapshot retains its own baseline.
- datasets/allsettlements/metadata.json and intercity_connectivity/metadata.json:
  source periods, versions, units and model-derived intercity times.
- backend/src/app/adapter/chat/: implemented map, comparison and calculation tools.

Verification: packaged DOCX runtime, bundled LibreOffice renderer; final pages inspected.
OOXML package comparison preserves every part except document.xml and its relationships.
Source template SHA-256: fc8b3f259f835d79d989995dc0461adb2a64bab372841bf2b14fe33d268475ca.
Authoring/QA workspace: /private/tmp/plexus-passport. Final intended layout is three pages:
identity/problem/validation; sources/method/coursework; results/limits/expert questions.

Limit: anonymous GitHub access could not be verified (web cache miss). Existing repository
URL is included as a pointer; current uncommitted code is not claimed to be published.
No product code changes, new model calls, commit, push or deployment performed.
