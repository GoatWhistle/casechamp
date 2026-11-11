# Server-rendered scenario comparisons

2026-11-11, feat/map-first-ui HEAD cdb2c2e. Uncommitted changes preserve other work.

The model previously composed Markdown comparisons, merged different scenarios into ranges,
exposed internal field names and generated wide cells. Plain tool tables were also hidden.

Implemented:
- manage_calculation(kind=table) accepts saved IDs and view=indices/routes/access. Server reads
  results; the model cannot submit cell values. Each scenario has its own caption and columns.
- Automatic review emits verified index tables before the prose stream. Table events persist in
  commentary and restore on reload. Regional Hansen jobs group by exact scenario inputs, version
  and network; names come from road geometry. Roads are also included in review evidence.
- Existing shared DataTable renders compact headings, numeric alignment and word-safe region
  names. A 349px table fits the desktop sidebar with all four index columns visible.
- Old completed commentary containing Markdown tables is replaced on screen using the read-only
  POST /api/v1/chat/calculation-tables endpoint. Original local history remains stored; the old
  prose/footnotes are not displayed beside the replacement. No model request is involved.
- Model guidance requests brief business prose, no Markdown comparison tables, method footnotes
  or internal field names. Underlying data and error states remain intact.
- OpenAPI/types regenerated. The existing optional ScenarioCard contract from the frontend merge
  is now declared in backend DTOs so schema generation preserves archive compatibility.

Verification:
- Backend Ruff and mypy passed. 406 unit tests passed; 48 integration tests passed before the
  final read-only table endpoint/grouping addition. Focused review tests passed after road-name
  enrichment. Frontend npm run verify passed: 479 tests, rules, types, lint, production build.
- Browser at 1440px with real saved calculations: 2 separate scenario tables. A saved old-style
  commentary was restored through the real API into 4 columns; zero model requests, no old
  arrow/range text, 349px table width. See legacy-restored.png. No mobile pass (user preference).
- Initial 414px table overflow was fixed with compact padding and a short change-column label.
- The first schema generator attempt waited for network; used the locally cached same-version
  openapi-typescript 7.13.0 CLI instead. No fabricated or manually written generated types.
- Impeccable launcher lacked writable engine cache; followed existing components and craft floor.
  UI-UX search data was absent; used the skill's general readability/accessibility rules.

Local API8007 PID86704, health OK; frontend5187 uses live source. No paid model call, commit or push.
Next: user can refresh the existing chat to see deterministic replacement of old comparisons.
