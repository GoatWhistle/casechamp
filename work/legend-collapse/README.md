# Collapsible map legend

User requested collapsing the floating map legend. Only map-legend.tsx and map-legend.module.css changed for product behavior. Reuse shared Disclosure, initially expanded; the complete header toggles scale and layer controls. Keep children mounted and inert/hidden when collapsed, preserving chosen layers and removing hidden controls from keyboard navigation. Header remains visible at all widths. Existing tokens and visual identity preserved.

Motion review: approve existing shared primitive: opacity/clip-path,160msenter/110msexit, interruptible transitions, instant keyboard behavior and reduced-motion tokens. No new animation implementation. No mobile checks per user instructions.

Changed-file Biome passed;451tests passed. Fullverify failed in concurrent road-stress/stress-card.module.css (surface consistency, missing space tokens, duplicate declarations); typecheck/build and lint also failed in the concurrent stress-card.tsx. These files were not changed by this task. Raw check logs are stored alongside this note.

Desktop browser checks at1440px use the real running API/UI. First capture waited for networkidle and timed out on map requests; waiting for the visible legend succeeded. First axe invocation needed an explicit browser context; corrected the harness. Screens show expanded and collapsed states; both visually inspected. Product docs/context templates have placeholder design text; incumbent components/tokens were used. Impeccable launcher could not install engine in its unavailable cache; ui-ux-pro-max UX CSV was missing, so its general reference and project controls supplied the guidance.

Final browser verification passed:295px expanded to70px collapsed, layer flags unchanged, Enter/Space/focus/tab behavior, reduced motion and rapid retoggle;0axe violations and0page errors. See browser.json.
