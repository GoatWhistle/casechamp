# Saved chat sessions, 2026-11-10

User: «и добавь чаты, новые старые, аккуратно только как то».

Scope: compact history picker in the existing map-chat header, a separate new-chat action,
first-question titles, search, active state, timestamps, and browser-local persistence. Existing
Popover, Button, TextField, ScrollArea and design tokens; no extra sidebar or backend API.
Desktop only, preserving prior no-mobile instruction. No commit/push or paid model request.

## Behavior

Conversation state moved to entities/chat; feature streaming addresses a session ID. Streams may
finish in a background conversation without changing the active chat or map. Provider requests
retain the shared serial queue. Drafts are per session. Reuse a blank draft when creating another
empty chat. Save individual versioned localStorage records, plus active ID; no history pruning.
Validate records, skip corrupt entries without overwriting them, show quota/read errors. Schedule
writes during idle time with task fallback and flush on pagehide/unmount. Interrupted main streams
restore as stopped, preserving text/artifacts. Storage belongs to this browser/origin, no sync.

Analysis commentaries now live in messages and restore without automatic model re-execution.
Interrupted commentary exposes retry. Saved commentary is included in model history. Completed
calculation cards do not automatically focus the map on reopening. No new animation: shared
Popover supplies its existing motion/reduced-motion behavior.

## Validation

- Focused frontend: 12 tests passed covering stream isolation while switching, queued requests,
  reload/remount restoration, independent drafts, blank-chat reuse, quota/retry, corrupt storage,
  separate records, preserved calculation cards and commentary restoration without model calls.
- Browser harness /tmp/check-chat-sessions.cjs, fresh browser context, real app5187 and controlled
  chat transport (no paid calls). Replayed saved Tyva analysis row for artifact persistence.
  Three chats, reload, search, per-chat draft, long title, Esc/focus return: passed. Exactly three
  user turns and one commentary request across switching/reload. No JS errors; zero axe violations
  in the picker. Screens /tmp/chat-sessions-1440.png and /tmp/chat-sessions-1920.png.
- Initial screenshot caught shared entrance mid-transition; final capture waits for animations.
- Initial rules found a width cap and literal persistence timer. Removed the unnecessary desktop
  width cap and scheduled saves through requestIdleCallback/task fallback. No motion-token abuse
  for storage timing. Official API reference consulted:
  https://developer.mozilla.org/en-US/docs/Web/API/Window/requestIdleCallback
- Full frontend verification status recorded below after completion.

Limits: only browser-local history; conversations lost before persistence existed cannot be
recovered. No live LLM quality test or mobile checks. Runtime backend remains owned by concurrent
storage/graph work; this change is frontend-only.

Final verification: `npm run verify` passed36rules, initial typecheck, lint and401tests/54files.
During the subsequent build typecheck, concurrent road API changes made `detail` required in
RoadView. Two fixtures in tests/entities/road-graph/road-render-data.test.ts (lines20/33) lack it.
The full command therefore exited2; did not edit the other task's new road test file. Chat files
passed their focused checks and the final browser replay (3turns,1review,3sessions,0JSerrors,
0axe violations). Final screenshots inspected at1440/1920; no further visual changes needed.

## Cleanup and deletion, 2026-11-10

Implemented explicit per-chat deletion with confirmation, last-chat replacement, abort of
its stream and browser persistence. Session switch/new/delete-active clears scenario overlays;
null corridor now removes its MapLibre layer/source. Legend exposes graph visibility and
manual overlay clearing. Existing backend calculations remain available independently.
Verification: frontend full verify passed 36 rules/411 tests/types/lint/build; existing chunk
size warning remains. Browser /tmp/check-chat-cleanup.cjs at1440 verified clear/new/switch,
graph hide, cancel/confirm deletion, reload and last-chat deletion.0JS/axe errors. Screens:
/tmp/chat-cleanup-history.png, /tmp/chat-cleanup-delete.png. No mobile or paid calls.
