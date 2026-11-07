# Project context

Project: transport connectivity index; product name and goal not selected.
Direction: «Транспорт и территории». Event name not supplied.
Deadline from supplied text: 10 November, 23:59; year and timezone unknown.
Defense: 13 November; year and start time unknown.
P0 scenario: not agreed; exploratory calculations complete, objective and scale await team choice.

## Current facts

| Topic | Status | Current fact | Evidence |
|---|---|---|---|
| Brief, 2026-11-06 | implemented | Supplied task preserved verbatim; requirements R01–R18 extracted; no scoring weights supplied | [source](../brief/sources/2026-11-06-task.txt), [requirements](../brief/requirements.md) |
| Deliverables, 2026-11-06 | verified against supplied text | Passport and artifacts by 10 November, 23:59; updated passport, 5–8 slides, speech up to 5 minutes and roadmap for 13 November | [submission rules](../brief/PLATFORM.md) |
| AI, 2026-11-06 | verified against supplied text | AI use and validation must be shown; AI-created materials must be attached | [R12 and R18](../brief/requirements.md) |
| Presentation excerpts, 2026-11-06 | implemented; copy verified | A2_citations.md copied from Downloads; passport length, artifact details and four unweighted expert criteria recorded; original slides not checked | [excerpts](../docs/A2_citations.md), [requirements](../brief/requirements.md) |
| Opening transcript, 2026-11-06 | implemented; copy verified | User-described opening speech copied unchanged from Desktop; audio not checked | [transcript](../docs/исаева.txt), [source record](../brief/sources/README.md) |
| Data acquisition, 2026-11-06 | implemented; verified | All 38 source rows accounted: 14 downloaded, 12 partial, 9 blocked, GAR deferred for disk, Open-Meteo needs parameters, OSM excluded by user; 185 local files, about 391 MiB | [catalog](../datasets/README.md), [coverage](../datasets/COVERAGE.md), [manifest](../datasets/manifest.json) |
| Data inventory | implemented | Original source table preserved; acquisition results and actual source limitations are recorded in datasets/; official organizer catalog link still absent | [inventory](../docs/istochniki_dannyh.md) |
| Git, 2026-11-06 | verified | Publication branch chore/project-research based on existing origin/main 5c81182; origin GoatWhistle/casechamp; all nonignored work prepared for publication, dataset raw/derived local | `git remote -v`, `git ls-remote --symref origin HEAD` |
| EDA, 2026-11-06 | implemented; verified | Computed city accessibility/scenario, municipal cohorts, regional bus intensities and geometric airport distances. City sample covers 52.59% of source census population; 2024 municipal paired cohort 1455. Earlier candidates; now economic-connectivity direction takes priority | [analysis](../work/eda/README.md), [checks](../work/eda/validate.py) |
| Economic direction, 2026-11-06 | user requested; framework proposed | GRP, development, criticality and traffic are the priority; economic inputs cover 85 regions in 2023; additional Kuzbass traffic 45 records found, period/5 inconsistencies require validation | [concept](../work/research/economic-connectivity.md), [traffic](../datasets/additional/traffic-counts-kuzbass/README.md) |
| Product choices | pending | Goal, territories, formula, scenarios and AI role are undecided | [questions](open-questions.md) |

## Pointers

- [Session](SESSION.md)
- [Open questions](open-questions.md)
- [Organizer materials](../brief/README.md)
- [Working artifacts](../work/README.md)
- [Product documentation](../docs/README.md)
