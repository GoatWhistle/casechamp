CREATE TABLE IF NOT EXISTS plexus_normative.service_directories
(
    id String,
    region_id String,
    category String,
    observed_at String,
    source_sha256 String,
    facilities UInt64
)
ENGINE = MergeTree
ORDER BY (region_id,category,observed_at,id);
CREATE TABLE IF NOT EXISTS plexus_normative.service_directories_facilities AS plexus_normative.regional_measurements_facilities;
