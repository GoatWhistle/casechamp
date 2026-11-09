# Audit of docs/ai-register.md

Scope: one-file read-only audit using `skills/docs-writing/AUDIT.md` and `SKILL.md`.
The page was copied by the parent into a detached worktree at
`a9c44a1dec8db814625d6ba0986b222f2207b380`; it is not committed here. The parent also
supplied the pending synthetic graph-compression test. Only this report is authored
in this pass. No product LLM, paid call, mobile check, ETL reconstruction, commit or
push was introduced.

## Findings and concrete recommendations

1. **Required evidence would not survive cleanup (lines 31–32).**
   The page links `presentation/plan.md` and `presentation/SPEECH.md`;
   `.claude/scrub-paths:15–16` explicitly deletes both. This is a confirmed conflict,
   even if the parent creates these pending files. Link actual submission copies
   under surviving `docs/submission/` or `docs/appendices/` and/or final exported
   slide/PDF artifacts. Preserve the disclosure and created materials: requirements
   R12/R18 and the organizer excerpt in `brief/requirements.md:54–56` require them.

2. **Tool disclosure currently conflicts with cleanup's trace check (line 12).**
   `cleanup_rules.py` includes `\bcodex\b` in `TRACE`.
   `cleanup_tree.py:scan` flags any matching text, `report_tree` makes traces fatal,
   and `strip_ai.py` aborts apply on failed preflight. An in-memory regex check
   confirms this line matches. Do not delete the truthful tool name to pass cleanup.
   Recommend a narrow exception for legitimate organizer-required tool disclosure
   in designated artifacts; keep generated-by signatures/commit attribution rules.
   This requires parent-owned implementation outside this page, followed by cleaned
   export verification. No cleanup operation was run during this audit.

3. **Four artifact links are pending in this snapshot (lines 31–34).**
   `node skills/docs-writing/check-links.mjs docs/ai-register.md` prints missing:
   `submission/passport.md`, `../presentation/plan.md`,
   `../presentation/SPEECH.md`, `appendices/README.md`.
   `presentation/src/slides/` is also absent, although backticks bypass the checker.
   Treat these as pending deliverables; do not remove legitimate AI disclosure.
   Until actual files arrive, replace “приложены”/“выпущенных” assertions with a
   clear current/pending status. After creation, check actual final submission paths.

4. **Some verification is asserted as completed without available evidence
   (table lines 23–24, conclusion line 36).**
   The audit snapshot has no national calculation report, passport, slides, speech,
   roadmap or PDF. Thus “Отдельный пересчёт, нормировка и проверка идентификаторов”
   and “синхронизация речи, просмотр PDF” cannot be verified here. These are pending,
   not proven false: the parent is doing national work concurrently. Require the
   resulting report/commands and actual artifacts before listing those checks as
   completed; otherwise label them planned. A text/model output and its verification
   should have separately visible statuses. “Реестр выпущенных материалов” is too
   strong while linked materials remain absent.

5. **“24 независимых сравнения” needs a precise scope (line 22).**
   The report and validator establish 2 seasons × 4 variants × 3 pairs on the same
   artifact, with an independent Floyd–Warshall implementation checking production
   Dijkstra `changed.total_h`/no-route outcomes. This is numerical method validation,
   not 24 independent empirical cases. Prefer “24 сравнения времени с независимой
   реализацией кратчайшего пути” and link the report. That report explicitly excludes
   HTTP/browser (`status=calculation_verified_not_http_or_browser`); the separate
   HTTP benchmark and browser test support distinct, narrower claims. Do not imply
   the 24-case protocol verifies HTTP, UI or source validity.

6. **Clarify the graph control and historical tool scope (lines 12, 21).**
   The supplied pending test compares a seven-node, three-way synthetic graph before
   and after omitting one way; it is not national raw-PBF equivalence. Add
   “синтетический контроль” to the row. The committed prior test only checked
   seasonal filtering and a reverse-oneway case; keep the expanded claim only with
   the new test. Codex is an appropriate tool name, not a named model dependency;
   do not invent a model version. If this purports to cover the entire project,
   confirm earlier Claude-assisted frontend work recorded in project context and
   disclose the actual tools used, rather than implying a complete tool inventory
   from this one implementation session. This is a completeness check, not proof
   that line 12's Codex statement is false.

## Verified claims and legitimate disclosure

- The deterministic runtime claim at lines 12–14 agrees with inspected
  `backend/src/app/main.py`, pilot routing/use case, national ETL modules and
  dependencies: no product LLM invocation or paid-model dependency found.
  Development assistance should remain disclosed as such.
- Frequency-control expected values 84/42/28 are correct. The corresponding named
  test passed. The code currently uses uncapped `84/f`; the prior cap is historical
  error disclosure, useful evidence of validation, not product-runtime behavior.
- Palma's equal-access, population-weight example gives 0.25 under the implemented
  fractional quantile boundary convention. That named test passed. This result is
  a numerical control, not a calibration against observed regional welfare.
- The newly supplied synthetic compression control passed. Reverse-oneway and
  seasonal-filter regression tests exist; no national graph reconstruction was run.
- Unknown-frequency alternatives can prevent proof of optimality, and the routing
  response exposes `warnings`/`optimality`; the stated limitation is supported.
- Committed pilot protocol, provenance and HTTP reports exist. Previous pass in
  this same worktree reproduced all 24 time/status comparisons against the shipped
  artifact. The HTTP report concerns sequential warmed-up loopback requests only.
- The source limitation in lines 41–44 is appropriate: no cost, causal VРП impact
  or present-day schedule/road-operability validation is established by the code.

## Seven-check outcome

| Check | Outcome |
| --- | --- |
| Needed | Keep. Required AI role, created outputs and validation evidence need a surviving submission record. |
| True now | Numerical/runtime claims supported; national/defense verification pending; scope refinements above needed. |
| Process story | Historical error rows are useful validation evidence for required AI disclosure. Preserve them; ordinary product-page history rules should not erase this purpose. |
| Links | Four missing artifacts, plus two paths explicitly scrubbed; treat as pending and relocate final evidence. |
| Water | No material filler. A status column or labels would prevent promising checks from reading as completed. |
| Tables | Four columns, parallel tasks, readable cell lengths. |
| Form | Required title, blockquote, read/related line, separators, claim/question headings and footer present. |

The skill's “No AI-tool names as author or source” rule should not be read as a
ban on a legitimate organizer-required tool-usage register. The page distinguishes
tool assistance from transport factual sources and team authorship. Preserve this
distinction; do not fabricate prompt transcripts, private reasoning or named models.

## Checks actually run

- Link checker: **four missing links**, listed above.
- Three selected in-memory root tests using existing Python and disabled bytecode:
  frequency control, Palma control and pending compression control: **3 passed**.
- Cleanup `TRACE` evaluated in memory on line 12: **matches**.
- Read-only code/report/path inspection.

No full test suite, HTTP benchmark rerun, Playwright execution, source-data ETL,
PDF inspection or cleanup/export was performed in this pass.
