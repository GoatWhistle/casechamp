CREATE TABLE IF NOT EXISTS plexus_normative.index_summaries
(
    region_id String,
    criterion_id String,
    run_id String,
    measured_at String,
    definition_sha256 String,
    unit String,
    weighting String,
    threshold_min Float64,
    threshold_max Float64,
    baseline_min Nullable(Float64),
    baseline_max Nullable(Float64),
    scenario_min Nullable(Float64),
    scenario_max Nullable(Float64),
    reference_points UInt64,
    measured_points UInt64,
    publication_version UInt64
)
ENGINE = ReplacingMergeTree(publication_version)
ORDER BY (region_id,criterion_id);

ALTER TABLE plexus_normative.index_summaries ADD COLUMN IF NOT EXISTS index_payload String DEFAULT '';
