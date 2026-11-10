# Removing region-specific demo scope, 2026-11-10

User: «удали следы этого ограничения про тыву вообще везде».
Branch feat/map-first-ui, HEAD c397ca6; existing uncommitted work preserved.

Removed regional-demo runtime: frontend entities/feature/dictionary, backend controller,
repository/usecase/domain, agent tools and registration. Retired related tests/ETL/export artifact.
Historical source and evidence retained under work/archive/retired-regional-demo, outside product.
Original research and regional raw input records preserved; no source graph/cache changes.

Every region profile now offers the same map scenario entry, with region+season+panel URL.
Agent capabilities expose national graph tools only. Regenerated OpenAPI and frontend types.
Updated current docs, README, presentation slides/speech and generated submission PDF/HTML.
Removed obsolete README banners; source metadata now describes national scope.

Verification: backend Ruff/mypy114files/170unit+integrationtests pass; frontend fullverify
379tests/build passes. Fewer tests reflect retiring obsolete subsystem tests, not skipping failures.
Browser1440/1920 tested18000000 and93000000: same scenario button/navigation, JSerrors0.
Screens /private/tmp/plexus-region-scenarios-{1440,1920}.png. Current API has no pilot paths.
Presentation build/speechcheck, finalrender and all7slideoverflowchecks passed.
Inspected scenario slide, regional screen and passport. Preserved source scope limitations:
82atlasregions; standalone /scenarios needs missing scenario_ru; single-edge fast path only.
Local backend8001 restarted, frontend5187 HMR. No paid model calls, commit/push/deploy.

Tool limitations: impeccable launcher cache permission failure; direct product/design context used.
Two wrong-cwd docs/speech commands failed before writing; rerun correctly. No unresolved check failures.
