CREATE DATABASE IF NOT EXISTS plexus_accessibility;
CREATE TABLE IF NOT EXISTS plexus_accessibility.runs (
    run_id String, created_at String, model_version String, source_model String,
    source_artifact String, graph_revision String, source_revision String,
    normalization Float64, normalization_kind String, regions UInt16, markets UInt16,
    point_count UInt32, frequency_status String, assumptions Array(String)
) ENGINE=MergeTree ORDER BY (created_at,run_id);
CREATE TABLE IF NOT EXISTS plexus_accessibility.results (
    run_id String, region_id String, season String, half_life UInt8,
    previous Float64, potential Float64, delta Float64,
    without_air Float64, without_rail Float64, without_water Float64,
    population UInt64, population_coverage Float64
) ENGINE=MergeTree ORDER BY (run_id,region_id,half_life,season);
CREATE TABLE IF NOT EXISTS plexus_accessibility.frequencies (
    run_id String, season String, mode String, source String, total UInt32, known UInt32
) ENGINE=MergeTree ORDER BY (run_id,season,mode,source);
