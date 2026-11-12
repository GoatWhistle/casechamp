CREATE TABLE IF NOT EXISTS plexus_normative.pedestrian_regions
(
    region_id String,
    region_name String,
    purpose LowCardinality(String) DEFAULT 'physical',
    revision String,
    published_at DateTime64(3,'UTC'),
    boundary_sha256 String
)
ENGINE = MergeTree
ORDER BY (region_id,published_at,revision);

ALTER TABLE plexus_normative.pedestrian_regions ADD COLUMN IF NOT EXISTS purpose LowCardinality(String) DEFAULT 'physical';
