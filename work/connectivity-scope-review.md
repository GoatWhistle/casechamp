# Connectivity scope review

## Scope explanation, 2026-11-11

Reviewed why city connectivity became a regional index. TASK.md permits regions;
Hansen and population aggregation existed in b1ea7af (7 Nov), formalized in
work/project-plan.md (9 Nov). Caveats: self-market contribution and hidden local
isolation, documented in docs/indices.md and alignment audit. No product changes
or runtime tests. Branch feat/map-first-ui, HEAD cdb2c2e. Next if requested: clarify
city-level versus regional presentation. Preserve concurrent work.

Pair/group index feasibility: current find_transport(kind=road) resolves two
settlements and model travel time; no dedicated selected-group index contract.
Explained feasible pairwise aggregation, excluding self-pairs and fixing scale.
No implementation or runtime verification requested/performed. Same branch/SHA.

## Prior chat state

## Floating chat window, 2026-11-11

> давай научим чат расширяться и сужаться, чтобы его двигать можно было, плюс закрть и открыть по иконке чатика в правом нижнем углу

Implemented movable/resizable chat, maximize/restore and bottom-right launcher;
closing preserves mounted state. Branch feat/map-first-ui, HEAD cdb2c2e.
[Checks and limits](../work/chat-window/README.md), docs/chat.md. Two verify runs
passed448tests; later concurrent road-stress changes broke global rules/i18n checks.
Desktop browser gestures/bounds/draft/focus passed. No paid prompts, commits or push.
Next: review at localhost5187; road-stress owner resolves unrelated checks.
Protected instructions exceed SESSION target and remain verbatim.
Final chat checks:28tests/8files and9-fileBiome pass. Later globaltypecheck interrupted
after2min during concurrentchanges; earlier fullverify typechecks passed.


