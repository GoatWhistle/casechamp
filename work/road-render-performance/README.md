# Road display performance, 2026-11-10

Branch feat/map-first-ui, HEAD c82ab1e. User requested faster road rendering/region clicks,
then consolidation into PostgreSQL or ClickHouse. Implemented locally, no commit/push/deploy.

- ClickHouse is running in `plexus-analytics-clickhouse-1`, localhost18123, isolated subnet.
- API localhost8001 was restarted with `.env.analytics` sourced (secrets ignored by Git),
  GRAPH_DIR=data, CHAT_ENABLED=true. PID76947 at startup; check lsof before managing it.
  Subsequent restarts MUST source `.env.analytics` to retain the faster display source.
- 50 tables, 125290049 rows copied and verified by row/NULL counts; source fingerprints
  guard repeat imports against same-row-count updates. Historical dates stored as strings;
  two nullable array columns are JSON strings. Original raw archives stay on disk.
- 95 atlas JSON documents copied with matching SHA256. Airport/legend work is concurrent;
  do not claim those changes as part of this performance task.
- 4305460 prepared lines represent all17393384 directed graph edges. Geometry is not
  mathematically simplified; adjacent segments are joined without losing vertices.
- Reference viewport old64779features -> new29765features. HTTP7.2549s -> .5742/.6990/.8073s.
  Before/after include gzip. Earlier15.3/21.5s timings had variable machine load.
- Coverage comparison: every old edge is present; same29765wayIDs. New answer includes
  whole lines crossing viewport, so count119681 differs from old118815directedmatches.
- Browser desktop was inspected; user actively operated it (Moscow/Yakutia selections).
  No reproducible FPS/interaction trace, no mobile verification. Avoid taking over active tab.
- Frontend cache minute retention, level/rounded-outward query keys, structuralSharing false,
  road click index by stablewayID, separate paint/geometry updates, manualfocus260ms.

Validation: backend Ruff/mypy src/180tests passed. Frontend verify389tests/build passed;
final camera/cache changes included in passing frontendverify. Full mypy . now also passes
126files; previously recorded corridor test errors were fixed by concurrent work. No paid model request. Evidence in docs/results.

Initial import failures were resolved: Docker address pool exhaustion (own subnet),
ClickHouse background pool setting, historicalDate32range, nullablearrays, exportmemorylimit,
and conservativefree-spaceguard. No source data deleted. Repeat import verified50tables.

Sources: official ClickHouse HTTP/Parquet docs, TanStack useQuery, MapLibre large-data guide,
and PostGIS ST_Intersects. No PostgreSQL comparison benchmark was run; storage choice was
based on workload, local resources, and actual ClickHouse response measurements.

Final checks: fullfrontendverify389tests+build; fullbackendmypy126files; focusedroad tests14pass.
Country/city/fareast API1.335/.185/.031s, allnonempty. Realimport regression covers1899date,
nullablearray andupdatedvalues withunchangedrowcount. Context compacted by moving5closedstatus
paragraphs behind session-before-closeout.md; active userquotes retained inprotectedsection.
