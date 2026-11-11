# Capacity ETL implementation

The source is the active legacy snapshot, not `plexus_refresh_graph`. Routing remains
undirected with a 72-hour road-search limit and legacy rail/air overheads; trunk links
remain present in the road scenario. Local manual links retain their source weights.
All graph nodes, settlement anchors, geometry and source populations stay fixed.

`prepare` attaches source partitions into the three `plexus_capacity_*` databases and
retains `reference_*` calculation tables. Frozen source tables have merges stopped to
avoid copying shared blocks. Stage output uses separate loading tables and exchanges
only after successful insertion. The active databases are never written by this package.

`weights` joins the completed traffic dataset by OSM way ID. Unknown traffic means
free-flow travel time; it does not mean a measured zero flow. Missing lanes use the
shared domain model's one representative lane per direction proxy. Ambiguous,
contradictory, unsupported-direction or unsplittable lane data retains typed source
counts but has `lane_data_usable=false` and no capacity. Ferries retain their source
speed and have no capacity. This implementation refuses confirmed traffic records
until a directional hourly-PCU profile has been reviewed for legacy aggregation.

The typed `road_costs` table feeds both ETL and runtime. Effective speed is calculated
from the shared domain travel time, including the posted legal ceiling. New edge time
is physical edge length divided by that effective speed. No bonus is applied to an
index or to a road class.

`matrices` uses the actual `GraphRouting` class against remapped candidate tables.
National market searches are shared across regions. It captures the runtime best-time
matrix directly and reconstructs road-only rows with identical Float32 rounding and
snap additions. District and population-threshold centre searches use the same road
CSR. All original source regions are retained in calculation tables, including source
regions outside the public atlas. Publication joins only the 82 atlas region codes.

`indices` rebuilds weighted regional/municipal values, inequality, and seasonal gaps.
`atlas` emits 246 records: 82 regions and three active legacy scenarios. Hansen's
normalization, CA log-Harris range, ARIA reference means and poverty cutoff are fixed
from the retained active road baseline. RAI and original geometric/economic fields
are retained. A new raw baseline is not independently rescaled to national mean 100.

## Manual commands

Set ClickHouse variables from the intended local configuration. From the repository:

```sh
PYTHONPATH=etl:backend/src .venv/bin/python -m road_capacity prepare
PYTHONPATH=etl:backend/src .venv/bin/python -m road_capacity weights
PYTHONPATH=etl:backend/src .venv/bin/python -m road_capacity matrices --workers 6
PYTHONPATH=etl:backend/src .venv/bin/python -m road_capacity indices
PYTHONPATH=etl:backend/src .venv/bin/python -m road_capacity atlas
```

The worker range is 1–48. Default is at most eight processes; no scaling guarantee is
made. Input and implementation fingerprints protect completed stages. An explicitly
requested `--restart-from` invalidates that stage and dependent checkpoints. Old
unsigned local checkpoints are explicitly marked as adopted. Activation and rollback
are separate parent-owned operations after national validation.

## Validation performed

- Fourteen unit tests exercise profile boundaries, frozen normalizations, time-based
  metrics, local-centre rerouting and actual legacy runtime/ETL matrix parity.
- A real ClickHouse fixture with 82 regions, three seasons and 492 synthetic point
  records verifies regional aggregation, inequality, RAI retention, seasonal gaps and
  repeated rebuild without duplicate rows. It passed on the primary server in its own
  temporary database; that database was removed.
- The same fixture initially failed on the isolated 18124 server with missing metadata
  files after an exchange. That environment failure is retained in the tool log; it
  did not alter production tables.
- These checks do not establish a completed national matrix run or field calibration.
  The parent owns full-run results, activation and final deployment verification.
