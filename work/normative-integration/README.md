# Integration, 2026-11-12

User approved importing repository datasets and existing aggregation, then publishing all changes to main.

Imported product delta 8d62824..bd32de3 (map-first-ui) with three-way reconciliation and 5daf681..bcc7301 frontend/brand/README updates. Local traffic search and protected context retained. No new municipal or agglomeration boundaries invented; existing region aggregation and municipal applicability metadata preserved.

Local ClickHouse: 36 normative tables, 9 criteria, 1278 facilities, 384 territory records, 30 normative bases, 84 regions, 24 directory memberships. Source facts arrays are empty; route snapshots and measured runs were not supplied. Seed evidence: seed/validation.json. Guarded seed script refuses populated catalogs.

Archived report fallback exposes exact saved scenario aggregates with report SHA/date/run identity and detail_available=false. No baseline or route fabrication. Current computed values take priority. Docker includes the same report. All nine live HTTP list endpoints return 84 rows; 745 numeric values in 756 rows: nine current explicit regulation/model/selection states take priority over archived values; two archived values are null. Original report retains all 754 numeric values. API evidence: live-api.json.

Checks: backend Ruff and mypy 479 files pass; prearchive full unit 876 pass, final changed archive/composition tests 15 pass; final full unit runs in commit hook. Frontend verify: 36 rules, types, lint, 546 tests, production build pass. ETL: 272 pass, 11 skipped (backend environment excluding road_traffic geography with missing pyproj and integration tests). Earlier broad ETL attempts failed collection due mismatched virtual environments; not counted as passing.

Automatic approval rejected the full integration suite against the working ClickHouse because some tests drop tables. It was not executed. Read-only live catalog and nine index API checks succeeded. Full route-dependent integration also needs the missing derived snapshots.

Runtime API8007 restarted PID63125; UI5187 existing Vite. Large raw local pilot dumps and merge backups remain local; source, JSON input datasets and compact measured evidence are published.

Browser: Chrome native accessibility confirms loaded map page, metric selector, chat/history and scenario tabs on127.0.0.1:5187. Existing stale-HMR tab recovered after fresh navigation. Native screenshot capture returned blank desktop; no screenshot evidence claimed.

Publication paused for additional authorized scope: mask everything outside highlighted region union and real municipal district selection. Search agent owns frontend; diff owns municipal/mask API; geography extracts actual admin_level=6 polygons from existing North Caucasus/South/Ural PBFs. No main commit/push yet.

Additional scope implemented: outside-atlas opaque raster mask with antimeridian handling; actual OSM admin6 boundaries, district click/zoom and keyboard selector. 511 polygons/20 regions imported, available source coverage partial. 33 Stavropol districts confirmed via live GET; Kemerovo correctly unavailable. Public source export datasets/municipal-boundaries with provenance/omission manifest. Final backend894unit/Ruff/mypy486 and frontend549tests/fullverify pass. Full suite initially caught duplicate test basename; renamed and rerun green. API PID67492.

Follow-up: centered national framing with uniform outside background; home-only resize recenter preserves manually selected view. Removed map transport-mode selector and visible municipal source annotations per user request. District layer visible at selected-region overview; empty data polls until imported. Historical national ADM2 fallback explicitly approved by user; provenance retained in stored data.

National district completion: 2325 polygons cover all82 UI regions; 577 current OSM polygons and1748 approved historical ADM2 polygons. Crimea35 andKemerovo31 current2026-11-11. Provenance retained in datasets/municipal-boundaries/expansion; safe importer etl/synthetic_traffic/municipal_import.py. Reimport inserts0/skips2325;4import/extractiontests pass. User clarified removal of the entire metric selector, not the additional-links metric itself. Metric options preserved; metric and season toolbar selectors removed.

Base road graph is now queried/rendered only while a region is selected. Reset clears its visible geometry and disables viewport fetching, including cached last geometry; scenario overlays retain their own behavior.

Map palette/context follow-up: warm sequential sand/terracotta colors shared with legend; selected region uses zero choropleth fill with source raster visible and distinct border, reset restores fill. Airports hidden below zoom5 and popups close on zoomout. Four contextual historical administrative outlines (Donetsk/Luhansk/Zaporizhzhia/Kherson) are separate noninteractive data; disputed metadata retained, no analytical IDs/index values. Outside mask includes them. LiveAPI verified84analyticalboundaryrecords+4contextualrecords; backend896unit/Ruff/mypy490 pass. Docker packages the same dataset. API8007 PID82632.

Preserved session detail before compaction:
Current: imported normative code/datasets from bd32de3 and UI/brand updates bcc7301, preserved adaptive traffic search. Local normative catalogs loaded; archived scenario aggregates exposed honestly (754 numeric/756 rows). Checks/evidence/limits: work/normative-integration/README.md. Map mask and real municipal selection implemented (511 polygons/20regions, partialcoverage). Backend894/frontend549 tests pass. Published main4111092; balanced map framing complete; district coverage2325polygons/all82UIregions; transport/season selectors andlinksmetric removed; API8007 PID82632/UI5187. Warm palette, selection clearsfill, airportminzoom5 and4display-onlycontextoutlines implemented; verification work/normative-integration/README.md.
Final frontend557tests pass.

Latest map steering: restored original teal seven-step palette per user; selected-region fill removal retained. Context areas now filled decoratively without index claims, fifth context Sevastopol closes southwest Crimea gap. Actual OSM Azov relation water polygon included in outside mask and separate water layer. Road viewport optional region_id requests all classes in selected bbox, capped250000rows with honest truncation. Worker intersects actual polygon/rings and retains matching OSM ways; neighbors show motorway/trunk/primary plus loaded connections belowzoom9, other neighbor roads onlyatzoom9+. Explicit scenario overlays unchanged. API8007 PID86380.
