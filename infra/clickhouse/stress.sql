CREATE DATABASE IF NOT EXISTS plexus_state;
CREATE TABLE IF NOT EXISTS plexus_state.stress_jobs
(id String, payload String, updated UInt64)
ENGINE = ReplacingMergeTree(updated) ORDER BY id;
CREATE TABLE IF NOT EXISTS plexus_state.stress_impacts
(id String, payload String, updated UInt64)
ENGINE = ReplacingMergeTree(updated) ORDER BY id;
CREATE TABLE IF NOT EXISTS plexus_state.stress_baseline
(version String, market UInt32, times Array(Float64), updated UInt64)
ENGINE = ReplacingMergeTree(updated) ORDER BY (version, market);
CREATE TABLE IF NOT EXISTS plexus_state.stress_point_impacts
(job_id String, point_id String, name String, region LowCardinality(String),
 population UInt64, node Int64, snap_km Float64, longitude Float64, latitude Float64,
 lost_markets UInt16, external_isolation Bool, delay_minutes Float64, worst_market String,
 markets Array(String), before_hours Array(Float64), after_hours Array(Nullable(Float64)), updated UInt64)
ENGINE = ReplacingMergeTree(updated) ORDER BY (job_id, region, point_id);

CREATE TABLE IF NOT EXISTS plexus_state.traffic_jobs
(id String, payload String, updated UInt64)
ENGINE = ReplacingMergeTree(updated) ORDER BY id;
