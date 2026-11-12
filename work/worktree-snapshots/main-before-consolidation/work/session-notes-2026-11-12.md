# Session notes moved from context, 2026-11-12

Status lines moved verbatim from `context/SESSION.md` during compaction. Quoted user instructions stay in the protected section there.

## Latest user instructions, 2026-11-11

The latest reset request supersedes older instructions to preserve local edits and root HTML.

## Current local runtime, 2026-11-11

Historical runtime: [record](../work/local-runtime-2026-11-11.md).

## Source tabs and map legend, 2026-11-11

Completed implementation and checks: [map controls record](../work/screens/map-controls-fix.md).
Protected instruction history exceeds SESSION target and is preserved verbatim.

## Legend border interaction, 2026-11-11

Completed map-controls history and verification: work/screens/map-controls-fix.md.

## Complete the map chat, 2026-11-11

Unified map chat and auth fix are published as Andrey in5aa8d1b/0612343 on feat/map-first-ui.
Runtime8080 is healthy;8000 belongs to MASP/modus. Details and limitations:
[chat workflow](../work/screens/chat-workflow.md).
Protected user instructions exceed the SESSION target and remain verbatim.
Final source checkpoint af825ca2b84e9a7d174bdb051c2fc2f385b93c82 on feat/map-first-ui,2026-11-12.
Title fix088c141 and scroll/paint fixaf825ca are committed as Andrey. Titles are initial-question
only; manual upward scrolling interrupts following; long answers have no blur/transform.
Frontend verify427 tests, backend Ruff/mypy and257 tests pass; five map E2E cases pass.
The deployed8080 build passes the long-source-answer browser check: stable title, stable reading
position, Home/End behavior and three inspected scroll positions without gaps. No live model
test prompts were sent. Code work is complete; publication target is origin/feat/map-first-ui.
Preserve command-scoped author/committer andreysk0304 <andreysk0304@yandex.ru>.
Limitations: full road rendering at1920 exceeded45s; /scenarios matrices remain unavailable.
Evidence, negative checks and runtime details are in the chat workflow record.

## Local launch on this machine, 2026-11-11

User: «подними проект»; correction: «Ветка последняя это мапс ui  чёт такое».
Branch feat/map-first-ui, HEAD 0c7cb89. Latest UI8080/API8000 and restored ClickHouse
are running; graph viewport and atlas HTTP checks pass. No commit/push. Runtime,
failed checks and limits: [record](../work/local-runtime-savelij-2026-11-11.md).
Protected instruction history exceeds SESSION budget and is preserved verbatim.

## Medical accessibility review

Reviewed user PDF and Logacheva2022; [findings](../work/research/medical-accessibility.md). Proposed service-specific pilot; no implementation. Branch feat/map-first-ui,0c7cb89. Next: choose scope if requested; PDF inputs are demonstrative.

## Territorial indices research and separate plan

Scope corrected: legally grounded indicators only; [revised plan](../work/territorial-indices-plan.md), broad survey archived in work/research/. Nine normative measures plus separate approved methodologies; current-edition gaps explicit. Branch feat/map-first-ui,0c7cb89; no code changes. Next: verify legal versions and pilot inputs.
