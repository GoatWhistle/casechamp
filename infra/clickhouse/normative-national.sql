CREATE TABLE IF NOT EXISTS plexus_normative.inventory_regions
(
    id String,
    name String
)
ENGINE = ReplacingMergeTree
ORDER BY id;

CREATE TABLE IF NOT EXISTS plexus_normative.national_inventory
(
    id String,
    region_id String,
    region_name String,
    name String,
    address String,
    categories Array(String),
    latitude Float64,
    longitude Float64,
    source_url String,
    snapshot_url String,
    source_sha256 String,
    observed_at String,
    geometry_method String,
    version UInt64,
    district String
)
ENGINE = ReplacingMergeTree(version)
ORDER BY (region_id,id);

CREATE TABLE IF NOT EXISTS plexus_normative.regional_measurements
(
    id String,
    region_id String,
    criterion_id String,
    saved_at String,
    payload String
)
ENGINE = MergeTree
ORDER BY (region_id,criterion_id,saved_at,id);
