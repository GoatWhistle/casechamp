# Chat diagnostics and capital attachments — 2026-11-11

Branch feat/map-first-ui, base HEAD cdb2c2e1108bde7ff37ab91f9d7907d05de2a897.
User requested debugging failed replies, then reported Moscow–Petersburg unbound.
Preserved unrelated concurrent changes. No commit, push, paid call or UI change.

Implemented correlated request/tool lifecycle logs, bounded credential-redacted
arguments/results, error message/cause chain/stack positions, final outcome/timing.
Uses configured uvicorn.error logger; no raw traceback locals, auth state or full
conversation dump. Unit failure reproduced missing start/message/end then passed.

Live unbound repro: inspect_bindings.py failed for both capitals. Names resolve to
market IDs45000000000/40000000000, absent from locations; market_cities already has
nodes3090046/1530067 and snap_h0. route_points now includes existing market attachments
when the ID is absent from locations. No source data or stored failed result changed.
Regression integration failed before query change and passed afterward.

validate_pair.py repeats actual calculate_connectivity with all3982closedways from
connectivity-7d8777d0b53c49a2835b6734c847712d. Result pair-validation.json:
8.061169267510195→13.897457029279394h, score6.118896752610524→0.8095138534591771,
relative decline86.77026453970134%. Both reachable. Road-only, fixed weights,
same selected whole OSM ways; no traffic, rail/air or field route verification.
Result is a validation artifact, not a new persisted chat calculation.

Checks: whole-backend Ruff/mypy passed;390unit/48integration tests passed.
API8007 restarted from existing .env.analytics with GRAPH_DIR=data, ROAD_WORKERS6,
CHAT_ENABLEDtrue; PID33945, healthHTTP200. Log /tmp/plexus-chat-debug-api.log.
Earlier PID21084 was already replaced by concurrent work (PID31326); graceful restart
targeted31326. UI5187 and secondaryAPI8817 unchanged. No paid model reproduction.
Initial uv command needed writable /tmp cache; localhost checks needed sandbox escalation.
