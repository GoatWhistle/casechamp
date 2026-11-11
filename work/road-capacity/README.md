# Road capacity implementation and local activation

Completed 2026-11-11 on feat/map-first-ui, base cdb2c2e1108bde7ff37ab91f9d7907d05de2a897.
No new commit, push or remote deployment. Existing user changes were preserved.

Product method and measured results: docs/road-capacity.md.
National validation, regional CSV, live API validation and final checks are in docs/results/road-capacity-*.
Source and stage fingerprints are in data/road-capacity/state.json. The activation journal
records UUIDs of all 14 table pairs. Keep plexus_capacity_* databases as rollback storage.
Do not use another output folder over those occupied databases.

The shared model uses one lane per allowed direction when lane counts are absent.
Unknown flow is unknown, with free movement. The current graph has zero confirmed
hourly-PCU flow profiles. Uniform 1800 PCU/hour/lane and BPR .15/4 are uncalibrated.
The existing 4,301,210-way topology and legacy undirected, 72-hour routing were retained.
No activation of the separate larger refresh graph occurred.

All 155,747 source origins were retained across three scenarios; 84 source regions
were computed, 82 regions/246 records published. RAI and raw demographic/economic
inputs did not change. Legal speed ceilings reduce speed on 62,182 ways. Public road
population-weighted mean Hansen changed from 99.1273023303 to 98.4536414763 on the
fixed original scale. A lower baseline is not an expansion benefit.

The schema migration preserved all 14 legacy jobs and their projected checksum
4085951559150447410. The old schema/data backup is plexus_state.road_jobs_before_capacity_v1.
Two stale persisted queued jobs were already cancelled by the running API; they were
reconciled after verifying an idle API. The migration and activation repeat safely.

The first API startup exposed a cache revision concatenation bug. BaselineCache now
accepts road_cost_model separately, preserving JSON revisions and older cache keys.
A regression test and fresh real startup passed. An early lane E2E run lacked its
fixture; another ran during a busy job, correctly finding the submit button disabled.
The final idle desktop suite passed all three tests. The live verification driver's
freight-scope assertion spelling was corrected; its rerun reused the completed lane
job rather than repeating routing. These issues are closed.

API PID50320 on8007, CHAT_ENABLED=true, GRAPH_DIR=data, ROAD_WORKERS=6.
Vite PID8599 on5187 proxies8007. Graphiti on8001 was untouched. Logs:
/tmp/plexus-capacity-api.log and /tmp/plexus-capacity-*.log.
No paid model calls were issued. No mobile checks were run.

Two full-graph validation jobs used five ways on the Volzhsky to Volgograd route:
664cbd1d3e5748c8898d816174585ab7 (lanes only),
c286723f4acc4dfa8218ed95e882d0d6 (hypothetical changed profile).
Their trips, rates and costs are synthetic validation assumptions, not observed
traffic or a construction proposal. New profile cut the travel time from 26.94 to
24.29 minutes and increased regional Hansen by0.0840561. Lane-only travel/Hansen/gross
benefits stayed identical. Freight mileage belongs to the selected fastest road path;
truck restrictions remain unverified. Manual freight inputs remain supported.

Completed checks: backend Ruff, mypy208files,300unit,45integration; frontend36rules,
typecheck,Biome,448unit,build;28capacityunit,1realaggregatefixture,1realmigrationfixture;
28nationalchecks,96independentpointformulas,252runtimebaselines;3desktopE2E withaxe.
Screens: profile-editor-1440.png and ../economic-appraisal/desktop-{1440,1920}.png.
1440 layouts were visually inspected. git diff --check and context budget passed.
All test outputs are in the /tmp logs above. There is no active verification job.
