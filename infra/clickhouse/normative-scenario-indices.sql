CREATE TABLE IF NOT EXISTS plexus_normative.scenario_index_summaries
(
    region_id String,
    criterion_id String,
    run_id String,
    policy_sha256 String,
    payload String,
    publication_version UInt64
)
ENGINE = ReplacingMergeTree(publication_version)
ORDER BY (region_id,criterion_id);
