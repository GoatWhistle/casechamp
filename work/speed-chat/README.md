# Speed-change calculation card

2026-11-11. User: «почему не вывели в чат это тоже как и удаление ?»

Cause: `recalculate_road_index` returned a job JSON but emitted no `calculation` event;
only named-corridor/bridge closures emitted the artifact. Reproduced with a failing
unit assertion: pending events were empty after a successful speed submission.

The road tool now preflights complete geometry by selected OSM way IDs and emits
job IDs, geometry and original change factors. The shared card labels increases,
decreases, closures and mixed scenarios accurately. Polling/results/map selection
reuse the existing component. Status queries also emit the card; recent-job discovery
recovers IDs missing from historical chat text. Existing stored messages are preserved.

Acceptance: `replay.py` reads the saved real Udmurtia job and ClickHouse geometry,
invokes the production status tool, and saves `acceptance.json`. No new calculation
or paid model request. 39 ways, 39 lines, summer, all factors1.2. Job
b217c537e87d4f02972134ee36b435a4 completed:98.58659925503848 to98.90432628894995,
delta0.31772703391146706, relative0.32228217253900127%. These numbers describe only
this submitted selection and model snapshot, not observed travel or traffic.

Desktop1440 browser replays that real event into the chat stream, reads the actual
job endpoint, asserts the title/result and selects its geometry on the real map.
Screenshot: `desktop-1440.png`. No mobile checks, per the user's standing instruction.
The first browser assertion expected two decimal places; the live UI correctly uses
four. Corrected the assertion and passed. Initial frontend regression expected an
unformatted number; changed it to the existing localized display format.

Checks: frontend verify423 tests/build; backend Ruff/mypy;211 unit tests and45
integration tests (ClickHouse). Schema generated from current app; first sandboxed
npx failed DNS, approved retry succeeded. No paid end-to-end LLM run. Backend reloaded
only after checking both scenario and analysis queues idle; existing jobs preserved.
No commit or push requested. Preserve concurrent appraisal and map color changes.
