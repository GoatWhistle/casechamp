# Synthetic traffic implementation, 2026-11-12

User authorized implementation after researching nationwide traffic data and housing-based demand.
Latest exact messages:

> поищи есть ли такой датасет для всей рф посвежее. Иначе давай поудмаем как можно их эмулировать от жилых домов условно
> деладелайдддделай
> ддделай
> деайltkfq

## Scope

Owned new files: etl/synthetic_traffic/, tests/test_synthetic_traffic*.py,
docs/synthetic-traffic.md, docs/results/synthetic-traffic-validation.json and this directory.
Appended docs index/design explanation and session context; preserve all unrelated dirty files.
No application routes, chat tool, frontend, primary graph/index weights or running service changed.
No commit, push, remote data publication or paid model/API calls.

Implemented CLI: snapshot, homes, collect-homes, run, publish.
- Immutable local directed road/population snapshot from ClickHouse.
- OSM explicitly residential areas, footprint × floors proxy, one floor when absent.
- Population-normalized house allocation, settlement fallback, local-road-node snapping.
- Spatial zoning without merging strongly disconnected components.
- Fixed reproducible passenger OD; low/base/high versions; destination population proxy.
- Joint MSA assignment, parallel roads, shared single-lane coupling, unmet demand and gap.
- Bounded contiguous corridor speed/capacity projects and <=5km manual new connections.
- Same-demand comparisons, saved edge-flow changes, immutable matrix SHA.
- Separate local ClickHouse database plexus_synthetic_traffic for housing/demand/flows/runs.
- National Geofabrik collector with sequential district processing and verified checkpoints.

## Source research

No fresh open national vehicle OD/count download confirmed in checked primary sources.
Do not claim universal nonexistence: Rosavtodor/SKDF access was incomplete.
- 2025 Avtodor section daily counts, published2026-01-26: https://mintrans.gov.ru/press-center/branch-news/8406
- Beeline commercial OD/custom CSV: https://ukhta.beeline.ru/business/analiz-dannyh/geoanalytics/
- MTS daily contract geoanalytics: https://geoeffect.ru/
- TomTom absolute-volume country coverage excludes Russia despite speed/time Stats coverage:
  https://docs.tomtom.com/traffic-stats/documentation/api/traffic-volume
- OSM Russia data up to2026-11-11T21:22:47Z at search time:
  https://download.geofabrik.de/russia.html
- Verified WorldPop Russia2025 modeled100m GeoTIFF,558M, dated2025-08-12:
  https://worldpop-public-data.soton.ac.uk/GIS/Population/Global_2015_2030/R2025A/2025/RUS/v1/100m/constrained/
  Not downloaded; existing settlement population used. 2025 is modeled, not a fresh census.
- GIS housing archive official help:
  https://cdn.dom.gosuslugi.ru/webhelp/topics/houses/och/t_download_archive-och.html
  Archive route documented; no whole-Russia bulk file downloaded/inspected.

Assignment references and current APIs checked through official AequilibraE, FHWA,
SciPy and Pyosmium documentation. Residential geometry is not itself observed occupancy.

## Actual local evidence

Existing North Caucasus2026-11-07 PBF produced634048 explicitly residential areas,
537551 with assumed one floor,142 geometry/floor failures. Full manifest forthcoming.
Pilot bbox41.55,43.8,42.25,44.95 includes17160nodes/44624directededges/161place records.
157bound populated places/532217people;344people unbound/outside snapshot.
10840homes allocate442604people;89613retain settlement fallback.
30zones/effective22.5km Cartesian grid;676OD pairs;8865.918321cars/hour generated,
4.365012cars/hour of production lacking external destinations retained separately.
These values are model inputs/outputs, not observed traffic or urban-flow validation.

Three loads × baseline/two projects converged at1e-5 tolerance:
- Existing5.169585671km corridor, ways301861394/178673480/302147425/583477758/583477757.
- +one lane/direction vs speed+20%; unchanged demand SHAa6059603b795159a1c14f1255abe4ca416d458ab18fcc8df78a42a7ddad622c0.
- Low:3.694879 vs15.590568 vehicle-hours saved over one modeled hour.
- Base:21.984167 vs25.242155.
- High:81.598285 vs42.243413.
- Gap9.76e-6..9.97e-6,13..455iterations; unserved assigned demand zero.
- Pair negative control07528000101→07724000001,1000cars/hour: both unrelated projects zero gain.
- Optimized predecessor-tree loading independently matched stored real flows at rtol1e-10/atol1e-8.

Local publication succeeded: runnevinnomyssk-housing-20261112-v1,
634048housing rows/676demand rows/401616flow rows. Source_id is Parquet SHA.
Raw/source/cache and full run artifacts remain in ignoreddata/additional/synthetic-traffic/.

## Checks and incidents

22 new unittest checks pass, logunit.log; Ruff check/format pass on owned code.
No backend/full UI suite run because backend/frontend source not changed by this task.
Live ClickHouse snapshot export/publication and real housing extraction exercised.
No full national traffic assignment or calibration against observed counts.
No browser/UI feature claimed; CLI only. External transit/boundary sensitivity absent.

Initial snapshot export failed on absentlegacy operating_season; now column introspected.
Arrow output names e.km/w.way_id normalized without changing values; SQL now explicit aliases.
Local read denied by sandbox first; approved read-only retry succeeded.
First collector was intentionally interrupted by PID identity check to enable range downloads;
completed Central checkpoint preserved. New collector checks ETag/Content-Range, four ranges
within one district file, then extracts and deletes only its downloaded temporary source.

## Running work and next actions

National collector tool session74081, outputdata/additional/synthetic-traffic/russia-homes-20261112.
Previous collector session19486/PID48285 intentionally interrupted; do not treat as current.
Refined comparison session68838/PID47839 completed. Publication session35234 completed.
Read collection.json before resuming; never overwrite verified or untracked outputs blindly.
Finish all districts, publish houses to own local database, verify distinct IDs/source counts,
refresh validation protocol and docs with final collection facts. Preserve failures/limitations.

Final housing filter/tree-loader run reproduced the exact demand SHA; 16 unit tests pass.
DB verification independently matched all nine vehicle-hour totals and634048unique pilot homes.
Connection hypothesis live test running toolsession75579; buildability explicitly unreviewed.

Live conditional133m connection completed at1e-5: demand unchanged, old forward edge3104.495→590.055cars/h; new link2514.440cars/h/C1800, overloaded.33.3945vehicle-hours saved but64overloaded directed edges remain. Buildability unreviewed; this is a load-transfer test, not a construction recommendation.

Candidate generator implemented and live checked:19existing-road variants/10connection hypotheses/0source-gap candidates atlimit10,highload. New tests cover bounds, source-gap triage, no-demand output and bad shapes;21unit checks pass. Source checksums and edge identities checked before reading baseline flows.


## Completion

National collection completed:9Geofabrik extracts, all timestamp2026-11-11T21:22:47Z.
6443907raw rows/6404792unique IDs;39115cross-extract duplicates removed in housing_current.
All nine source counts and numeric latitude/longitude/area sums match Parquet in local CH.
The complete collection registry is stored in housing_collections; activation excludes the
older pilot housing source. Repeating national publication skipped all completed source files.
Fresh national housing pilot run completed:32zones/15169used homes/456783allocated people,
75434fallback people. Synthetic demand hash7fa2428aa96c21427899b3d7e73e4750490c361fef5331b3a586bcad5207be39.
This is still a local-window traffic run using national housing inputs, not a national assignment.
Country source folder and source timestamps/hashes retained; only own transient PBFs removed.

Final source export v3 exactly matches every pilot network array. Daily regional trip profile
now excludes baseline destinations farther than4h; all original pilot times<=3.347741h and
old pilot matrix SHA reproduced unchanged. Prevents forced daily trips to remote destinations.
22unit tests pass. Final owned Ruff checks, format and documentation links checked.
Conditional new-connection run also published locally:676OD/89250flowrows.
No processes from this task remain after collection/model/publication completion.
No commit/push, public release, application restart, paid call, browser or UI integration.

Final source manifest, national numeric equality, latest-housing smoke and connection results are included in docs/results/synthetic-traffic-validation.json. Source audit and CLI instructions are in docs/synthetic-traffic.md. No outstanding task processes or required checks. Next integration work would expose this CLI calculation module through application tools/UI and validate against observed counts.


## Preserved session checkpoint, 2026-11-12

Implemented CLI/house allocation/joint assignment/bounded candidate search/local CH publication.
[Scope, owned files, commands, evidence and incidents](../work/synthetic-traffic/README.md).
National housing complete:9extracts, OSM2026-11-11T21:22:47Z;6443907raw/6404792uniqueobjects.
CHplexus_synthetic_traffic stores sources, current deduplicated housing, OD and two pilot runs.
22unit checks/Ruff/format/docs links pass;9pilot cases converge at1e-5; unrelated pair gains zero.
[Method](../docs/synthetic-traffic.md), [protocol](../docs/results/synthetic-traffic-validation.json).
Fresh-country housing smoke and all-source numeric equality verified. No running task processes.
No national traffic assignment/calibration or chat/UI integration. No commit/push/restart/paid calls.
Existing unrelated dirty work preserved. Branchfeat/transport-scenarios-update HEAD986ae0f5ee754b9e98f25e2e608b5bc37cbad507.
Next optional scope: application integration and observed-count calibration; current CLI/data task complete.
