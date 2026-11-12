# Regional physical results at full scale

Status: implemented and locally deployed on8083/API8003. Numeric cards use compact cache; the physical view uses descriptor, page, point and map queries. All526926Krasnodar origins remain available. Verification: docs/results/normative-paged-results-validation.json. Shared ClickHouse global memory pressure remains a recorded limitation.

## Contracts

- Descriptor: immutable run metadata, comparison, mode/unit, profile, counts and saved date. Never includes all rows.
- Row page: run/stage, bounded page size, total reference count, stable position ordering and original AccessRow DTOs. Counts and scenario deltas cover the complete run, not the page.
- Single origin: run/stage/id returns the saved row for map selection and details independently of the table page.
- Facility search/page: saved run facilities with original provenance and stable pagination.
- Map view: run/stage/bounds/zoom returns bounded grid aggregates. Each aggregate carries reference count, measured count, unknown count and cost range. Sum of cluster counts must equal all saved references within the viewport; no population invented. One-reference cells may expose the real origin id; cluster clicks zoom, individual clicks open a real origin.
- Route lookup: fetch only the selected saved origin/facility and run metadata before graph reconstruction. Preserve revision and cost replay checks. Legacy JSON snapshots remain readable through explicit fallback.

## Interaction

The paths action opens a bounded map view and the first table page. Pagination, sorting and search run on the server. Changing map bounds refreshes visible aggregates without retrieving the full run. Selected-origin details use their own query. Source/mode notes and saved profile remain visible. No page-level percentages substitute for the complete numerical index.

## Verification

Use the actual large Krasnodar run plus Nenets and one car service. Verify independent total counts, disjoint adjacent table pages, stable sorting, antimeridian bounds, cluster count conservation, unknown paths and exact route replay. Browser1440/1920 must show real paths after selecting an origin, with bounded network responses, no whole-array measurement GET, no JS/axe errors or overflow. Do not claim national completion from only a small-region check.
