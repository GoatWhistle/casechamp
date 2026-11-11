# Compact closure result, 2026-11-11

User: «оформи теперь это всё минималистично и удобно для агента».
Follow-up: «тут не все регионы рисуй, а только затронутые».

Implemented shared summary API/SQL, region-filtered totals, pending-null semantics,
compact agent replies (5 examples; full geometry remains in card), impact default for
close_selection, explicit Hansen opt-in, collapsed secondary UI and affected-region selector.
No model weight or index formula change. No paid model call.

Scope: frontend/entities/road-stress, closure calculation display and RU dictionaries;
backend stress DTO/store/jobs/controller, stress tools and small scenario routing/wiring edits.
Existing concurrent dirty work preserved. No commit/push/deployment.

Checks: backend Ruff check, mypy260files,376unit and46real ClickHouse integration passed.
Frontend verify passed (461tests). Four desktop Playwright scenarios passed on real API:
keyboard/reduced motion/axe, persisted reload, actual detour, selected region summary/axe.
Later region-selector correction gets a focused browser recheck.
Global Ruff format --check failed on77preexisting/modified files; no mass formatting applied.
Initial uv command could not access its cache; checks used installed .venv executables.
Initial local-network checks were sandbox-blocked; approved local checks succeeded.
First summary request raced API startup; after ready it returned correct persisted values.

Evidence: compact-summary-validation.json (real714-way scenario), compact-ui-checks/ screenshots.
Novgorod:3713affected,583386exposed,64newlyisolated,1414isolatedresidents,max207.3069minutes.
National:146522affected,124932367exposed,96isolated,5388isolatedresidents,81regions.
Broad any-market criterion is exposure, not traffic; no physical-isolation assertion.

Runtime: owned validation API8817 PID22680/session11312, preview5190 served from
/private/tmp/plexus-stress-preview-20261111. Main8007/5187 left running.
Latest frontend build copied to preview after checks. Mobile checks omitted per user instruction.

Final region correction: dropdown options exactly match positive-settlement regions in
saved API job; aggregate label «Все затронутые». Final frontend verify461tests passed.
A newly added test's Russian region literal initially failed cyrillic rules; it now reads
the region from the real saved route fixture. Focused selector+axe browser recheck passed.
