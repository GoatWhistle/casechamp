CREATE TABLE IF NOT EXISTS plexus_normative.regional_directory_memberships
(
    region_id String,
    category String,
    facility_id String,
    service String,
    scope_source_url String,
    scope_source_sha256 String,
    version UInt64
)
ENGINE = ReplacingMergeTree(version)
ORDER BY (region_id,category,service,facility_id);
