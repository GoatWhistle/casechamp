# Recent chat title scrolling

2026-11-12, feat/transport-scenarios-update@5daf681.
User: «пусть прокручивается если справа не помещается».
Recent chat titles use horizontal ScrollArea; grid and content tracks may shrink.
Browser 1440px: title viewport236px, content363px, scrollLeft100 confirmed.
Screenshot /tmp/chat-recent-scroll.png. Verification /tmp/chat-recent-scroll-verify.log.

Verification: rules, initial typecheck, lint and 502 tests passed. Final build blocked by concurrent unrelated analysis-panel.tsx:53 missing traffic:developmentHint translation key. Next: rerun build after that change is resolved.
