CREATE TABLE IF NOT EXISTS plexus_atlas.municipal_boundaries
(
    id String,
    region_id String,
    name String,
    admin_level UInt8,
    osm_relation_id Int64,
    geometry_json String,
    bounds Tuple(Float64, Float64, Float64, Float64),
    source_url String,
    observed_at String,
    source_sha256 String,
    region_assignment String,
    region_overlap_fraction Float64,
    version UInt64
)
ENGINE = ReplacingMergeTree(version)
ORDER BY (region_id, id);
