# Project context

Plexus — transport connectivity atlas for regional policy analysts, focused on settlements,
seasonal links and access to centres/markets. Case A2, «Транспорт и территории».
Current implementation: React/Vite frontend + read-only FastAPI over exported JSON;
separate DuckDB/OSM calculation pipeline. Russian UI, one light theme per user instruction.

## Current facts, 2026-11-09

| Topic | Status | Fact and evidence |
|---|---|---|
| Workflow | verified | Only main / origin/main after integration; baseline SHA 81b6524. User explicitly requires work on main. |
| Task alignment | audited, incomplete | R01–R18 mapped; no requirement labelled stand-verified in this audit. [Audit and priorities](../work/audits/project-alignment/2026-11-09.md). |
| Original PDFs | read | [Case A2](../brief/sources/2026-11-09/case-a2.pdf), [transport briefing](../brief/sources/2026-11-09/transport-connectivity.pdf). Index, comparisons and recalculated transport changes are the core output; a web app or LLM inside the product is not required. |
| Atlas API | verified in process with real files | 82 regions, 155412 settlements, 997 links; Tuva 7 links. [Evidence](../work/audits/project-alignment/evidence.md). |
| Index | code only; missing in app | etl/indices.py exists; data/ absent; indices.json empty; API status=missing. Current frontend metric selector has no Hansen. |
| Scientific risks | code-reviewed | Seasonal OSM edges not removed from common graph; wait cap makes 1/2/3 weekly departures equal; Palma counterexample fails; district-centre proxy is not hospital access. See audit. |
| Scenarios | partial | EDA contains one hypothetical Kostroma–Obninsk change under a different formula. Summer/winter calculations do not by themselves prove a preferred improvement for the final pilot. |
| Validation | scoped | Merge frontend verify: 372 tests. Backend unit rerun in audit: 106 passed. Full ETL, all-source verification and current browser path not checked. EDA validation blocked by missing ignored raw ZIP. |
| Submission | unverified | No team passport, final slide deck, roadmap or submission receipt found here. Root speech.md is a briefing transcript. |
| Deadline | conflicting sources | Supplied general rules say 10 Nov 23:59; preserved SESSION report says organizer reply 23:39. Timezone and exact primary message require verification; defense 13 Nov. |

## Pointers

- [Session and protected instructions](SESSION.md)
- [Open questions](open-questions.md)
- [Requirements](../brief/requirements.md)
- [Product documentation](../docs/README.md)
- [Prior EDA](../work/eda/README.md), [integration](../work/integration/2026-11-09.md)

Next priority: settle one target decision/pilot; restore inputs; fix seasonal routing and waiting;
calculate baseline and transport interventions; expose results; package submission and AI evidence.

Implementation plan: [work/project-plan.md](../work/project-plan.md). User selected two levels, interactive pilot calculation and explicit assumptions for incomplete data.

Implementation started: [progress](../work/implementation-progress.md). Settlements and intercity source Parquet restored; national download/extraction ongoing. Model controls pass (13 local tests), full recalculation pending. Deadline primary message preserved in brief/QA.md.
