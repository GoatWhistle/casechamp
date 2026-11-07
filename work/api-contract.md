# API contract v1 (frontend ↔ backend)

Date 2026-11-08. Read-only API over the exported atlas data. Base path `/api/v1`. JSON, UTF-8.
Errors: `{ "code": "snake_case", "message": "English text" }`; 404 `region_not_found`, `link_not_found`; 422 `validation_error`.
Ids are strings (OKTMO). Numbers are numbers; unknown values are `null`, never 0. Coordinates `x`, `y` are in the projected SVG space of `geo/region-paths.json` (same projection as `frontend/atlas/scripts/prepare-regions.py`).
Season enum: `all | summer | winter`. `all` counts every link including unknown season; `summer` = season in (summer, all); `winter` = season in (winter, all).
Mode enum: `air | river | winter_road | ferry | ice_crossing | pontoon_bridge`.

Data source: `frontend/atlas/public/` (`atlas.json`, `additional.json`, `additional/regions/<id>.json`, `geo/region-paths.json`, `indices.json`). Backend reads it via setting `DATA_DIR` (default: repo `frontend/atlas/public`).

## Endpoints

| Method, path | Response |
| --- | --- |
| `GET /health` | `{status:"ok"}` (template) |
| `GET /overview` | `{regions, settlements, population, links, links_by_mode: {mode: n}, links_by_season: {summer, winter, all, unknown}, companies, revenue_rub, index: IndexStatus}` |
| `GET /geo/regions` | `{view_box: "x y w h", regions: [{id, name, path}], missing: [{id, name}]}` |
| `GET /regions?season=` | `[RegionSummary]` sorted by name |
| `GET /regions/{id}?season=` | `RegionDetail` |
| `GET /regions/{id}/links?season=&mode=` | `[Link]` |
| `GET /regions/{id}/settlements?q=&sort=population|name|companies&order=desc|asc&limit=50&offset=0` | `{total, items: [Settlement]}` |
| `GET /links/{id}` | `Link` |
| `GET /search?q=&limit=8` | `{regions: [{id, name}], settlements: [{id, name, region_id, region_name, population}]}` (q ≥ 2 chars, case-insensitive, «ё» = «е») |
| `GET /seasons/winter-roads` | `[WinterRoad]` from `additional.route_seasons` |
| `GET /sources` | `[Source]` atlas sources plus `additional.sources` |
| `GET /index` | `IndexStatus` with methodology |

## Schemas

- `IndexStatus`: `{status: "ready"|"missing", reason: string|null, formula: "A_i = Σ M_j · exp(−β · t_ij)", half_life_hours: 2, markets: 180, components: [{key, title, description, source}]}`. Status is `missing` while `indices.json` is empty.
- `RegionSummary`: `{id, name, settlements, population, links, links_season, companies: int|null, revenue_rub: number|null, hansen: number|null, has_geometry: bool}`.
- `RegionDetail`: `RegionSummary` + `{path: string|null, bbox: [x, y, w, h]|null, links_by_mode: [{mode, all, summer, winter}], economy: {company_rows, strict_rows, strict_revenue_rub, fns_matched_rows} | null}`.
- `Link`: `{id, region_id, mode, season: "summer"|"winter"|"all"|null, from: Endpoint, to: Endpoint, km: number|null, freq_per_week: number|null, freq_assumed: bool, freq_note: string|null, vehicle: string|null, confidence: "high"|"medium"|"low"|null, source_url: string|null, source_date: string|null}`; `Endpoint = {id, name, x: number|null, y: number|null}`.
- `Settlement`: `{id, name, region_id, population: int|null, x: number|null, y: number|null, companies: int|null, revenue_rub: number|null}`.
- `WinterRoad`: `{district, route, road_km: number|null, opening_date: string|null, closure_date: string|null, weight_limit_tonnes: number|null, season_end_year, report_date, source_file}`.
- `Source`: `{id, title, period: string|null, url: string|null, note: string|null, rows: int|null}`.
