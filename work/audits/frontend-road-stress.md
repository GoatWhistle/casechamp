# Frontend audit: national road stress

Scope: five dimensions for `/?panel=scenario&stress=<id>`, Russian light desktop UI,
1440×900 and1920×1080,2026-11-11, sourceHEADcdb2c2e with uncommitted implementation.
The user's explicit instruction excludes mobile checks. Existing tokens/components are
used because PRODUCT.md/DESIGN.md still contain template placeholders.

## How checked

`npm run verify`:36rules, typecheck/lint,460tests/build passed including final history test.
Targeted Playwright:3passed on immutable preview5190, including axe on empty workspace,
saved job reload and a real HTTP detour from Torzhok to Veliky Novgorod. No mocked API.
Screenshots in work/road-stress/browser-release-results inspected manually.
Final3E2E passed in10.6s, with Enter toggling history, focus retained and reduced motion enabled.
Original workspace/result screenshots retained in work/road-stress/browser-results.
Initial failed tests and HMR interruption retained in browser-final-results.

## Summary

| Dimension | Score0–4 | Evidence/limit |
| --- | --- | --- |
| Motion | 3 | Shared Disclosure/Combobox, camera duration token/reduced motion; no full CLS measurement |
| UX/scenarios | 3 | Real search, route comparison, persistence and cancellation verified; first route is slow |
| Visual system | 3 | Existing Card/Button/Select/tokens; explicit stress legend separates it from atlas index |
| Air/rhythm/scaling | 3 | Desktop screenshots inspected; full national list reduced to region selector/10-row pages |
| Copy/polish | 3 | Source exposure is explained; zero result shown honestly; no fabricated ROI/traffic |

## Findings

P0: no outstanding failures in the tested desktop scenarios.
P1 fixed: closure geometry vanished when switching result views of the same job.
Regression test now preserves same-job geometry and rejects stale geometry from another chat.
P1 fixed: all82region buttons created excessive vertical content. Region selector and pagination
use existing controls; route form appears before the point list.
P1 fixed: 4px card padding cramped the text. Changed to existing16px spacing token.
P1 fixed: overlay had no separate legend. Red closure/grey before/blue detour explained on map.
P1 final refinement: floating chat obscured route bounds. Camera now reads the panel bounds and
fits into the larger free side; final1440screenshot inspected after3E2E passed; path fits the free map area.
P2 open: initial route/baseline can take minutes under load. Jobs expose progress/cancel;
route repeat uses bounded cache. No latency guarantee is claimed.

## Before/after

- Before: browser-results/stress-result-1920.png, zero result with cramped padding.
- After: browser-release-results/stress-result-1920.png, national summary and explicit legend.
- Before route: browser-release-results/stress-detour-1440.png, route partially under chat.
- Final route: browser-camera-results/stress-detour-1440.png after padding refinement.

## Not checked

No mobile, other themes/languages, real screen reader, slow network, full CLS or200% browser zoom.
Impeccable engine unavailable during initial session; existing shared components and repository
rules were applied directly. No production deployment or paid semantic model test.
