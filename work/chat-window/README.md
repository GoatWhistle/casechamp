# Chat window verification, 2026-11-11

Implemented floating chat over the full-width map. Drag header, resize lower-left
corner, maximize/restore, close and reopen via bottom-right launcher. Preserves mounted
chat and scenario content, draft and window geometry while staying on the page.
Bounds re-clamp on workspace resize. Keyboard arrows use 10px steps, Shift uses 40px.
Minimum 400×480 (or available workspace); 80px bottom strip reserves the launcher.

Browser: http://127.0.0.1:5187/, Chromium, real API, 1440×900 and 1920×1080.
Passed pointer drag/resize, close/reopen with draft and focus, maximize/restore,
keyboard movement, tabs, minimum dimensions, bounds, viewport resizing. No page errors.
No paid prompt sent; stream continuity follows preserving the mounted chat hook.
No mobile checks as requested earlier. Screenshots are saved here.

Two full frontend verify passes succeeded with 448 tests before concurrent road-stress
changes appeared. Latest global run then failed on an unregistered stress.json namespace;
a subsequent rules run flagged stress-card.module.css surface/unknown spacing tokens/duplicate
list declarations. These files are outside the chat changes and were left to their owner.
Build had existing PostCSS `from` and chunk-size warnings. Initial UI-context launcher
unavailable; read local design docs and skills directly. UI UX dataset missing.

Initial 360px minimum clipped a multiline draft; increased to 480px. A first browser
assertion sampled entrance animation and differed by 1px; rerun awaited completion.

Final changed-file Biome check passed (9 files). A later whole-project typecheck
was interrupted after more than two minutes with concurrent typechecks and evolving
road-stress source; the two earlier full verify passes are the completed typecheck evidence.
Final chat-specific tests: 8 files, 28 tests passed. git diff --check passed.
