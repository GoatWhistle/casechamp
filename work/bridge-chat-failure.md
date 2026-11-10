# Bridge chat failure, 2026-11-10

Request: user pasted the Saratov/Engels bridge dialogue ending in a failed response
after choosing both bridges. Branch feat/map-first-ui, HEAD
6ca0e3e70f299312b3ae3764c93353bde8b9e9e7. No commit or push for this fix.

API log `/tmp/plexus-local-api.log` records `UnexpectedModelBehavior` at
`resolve_road_corridor`, caused by settlement ambiguity exhausting ModelRetry.
Read-only replay against ClickHouse returned 21 substring matches for Saratov,
three for Engels, and zero for the region-qualified Engels name. A second issue:
road lookup for Р-228 included an empty reference alongside the valid reference.

Changed corridor settlement lookup to exact normalized names with separately
matched comma-separated regions. Exact full labels take priority, actual homonyms
remain ambiguous. Ignore empty road-reference aliases. Return InvalidQuery as a
structured unresolved tool result, rather than spending the tool retry budget.
Agent instructions distinguish bridge selection from whole-highway closure and
require combined edits for a combined effect.

Validation: regression tests failed before changes; final backend Ruff and mypy
passed, 184 unit tests and 40 integration tests passed. Real ClickHouse replay
resolved Saratov and qualified Engels uniquely; unqualified Engels returned both
actual choices without ModelRetry. No paid LLM test was run. No numerical bridge
closure result is claimed: precise bridge-way selection remains unverified.

Unrelated accessibility-model implementation, generated schemas, publication and
road-refresh edits were already in progress and have not been reverted. An initial
mypy failure in that concurrent domain module cleared in the final verification.
Before API restart, no running/queued road jobs were present; one road analysis was
paused. Existing browser chat history was not edited.

API8001 now runs the fix in persistent exec session10087 with CHAT_ENABLED=true and
the existing `.env.analytics` configuration. Health returned OK and seven stored
road jobs were restored. The initial detached subprocess did not survive tool exit;
the persistent session replaced it successfully. The previous PID38419 was stopped
gracefully; its historical failure logs remain in `/tmp/plexus-local-api.log`.
