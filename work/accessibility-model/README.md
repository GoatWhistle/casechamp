# Potential accessibility implementation

Authorized 2026-11-10 after the index/transport discussion. Preserve active indices and concurrent road refresh.

- Versioned potential accessibility on the same active source snapshot and fixed normalization as the comparison.
- Planned departures omit schedule waiting, retain travel/terminal costs; unknown frequency stays unknown.
- Compare summer/winter at half-lives 2, 4 and 8 hours. The latter are sensitivity parameters, not calibrated behavior.
- Compute marginal removal of air, rail and water (river/ferry) independently; effects are not additive.
- Recalculate local links, unify ferry boarding overhead, preserve source limitations and report frequency completeness.
- Persist completed runs and regional results in dedicated ClickHouse tables. Source revision changes mark the comparison stale.
- Show an additional comparison in the existing region workspace. Existing map ranking and road scenario jobs retain their published model.

Active source inspection: atlas uses hansen-release-20261107/data-20261107 (246 rows), not hansen-frequency-v2. Trunk waits are absent in this snapshot; local waits are capped at 24h. The 84h rule belongs to the new national pipeline. Do not describe it as the current UI's behavior.

## Verification and recovery

- Backend: 187 unit tests passed; full mypy/Ruff passed. Frontend verify: 415 tests, 36 rule checks, typecheck, lint and build passed. Existing PostCSS/chunk-size warnings remain.
- Four numerical ETL tests cover disconnected-population weighting, one ferry boarding across multiple segments in both directions, disconnection after local-air removal and directed trunk costs.
- Independent previous-index reconstruction on 82 regions: maximum absolute summer difference 0.0000021771863 points.
- Failed first attempt: explicit alias for joined `region` missing; fixed before publication. No partial result was published.
- Joined national previous-index query exceeded ClickHouse's 2.33 GiB global limit. Bounded Arrow streaming with one query thread reproduced the published values without the join. `readonly=2` permits per-query resource settings while remaining read-only.
- Summer full/without-air/without-water checkpoints were retained; numerical routing/aggregation unchanged across recovery. `checkpoint-reuse.json` records migration to the updated cache key after changing only legacy-result reading, formatting and pinned-source selection.
- Active calculation uses `--source-revision d974f339a31d03fd`; new log `calculation-resumed.log`. Inputs remain in dedicated ClickHouse snapshot, not in restored runtime files.
- Browser inventory is empty; use project Playwright for desktop visual QA. No mobile checks, paid model calls or publication by this task.

## Completed 2026-11-10

- Run `78aac55e5bae432d99ea8be0600a584a` persisted successfully: 492 results, 12 frequency records, 82 regions, 155412 points, 180 markets. Source snapshot `d974f339a31d03fd` is retained. Source is current at the browser verification time.
- All 492 persisted results have finite values and valid coverage; zero mode-removal monotonicity violations. Previous summer/winter indices reproduce the source within 0.00000218 points. Evidence: `docs/results/potential-accessibility-validation.json`; interpretation and national weighted effects: `docs/potential-accessibility.md`.
- Full backend storage/API integration: 43 passed, including the new 82-region checks. Both desktop E2E scenarios at 1440/1920 passed, with zero axe violations or browser page errors. Screenshots visually inspected: `comparison-1440.png`, `comparison-1920.png`. No mobile checks.
- E2E first failed because JSON import lacked its type attribute; then duplicate card/table accessible names were detected and fixed with a separate table caption. Final tests pass without disabling any accessibility rule.
- Final numerical checkpoint reuse after formatting-only changes is recorded in `final-checkpoint-reuse.json`. Completed report retains its original calculation cache directory; the current-code cache contains only equivalent numerical checkpoints.
- Exact timetable index remains unavailable; unknown frequencies are not imputed. This model is an additional planned-trip comparison, with the retained source limitations. Active road refresh and scenario jobs were not restarted or interrupted. No commit/push/deploy was performed by this task; concurrent publication committed some files independently.
