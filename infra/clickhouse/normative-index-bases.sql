CREATE TABLE IF NOT EXISTS plexus_normative.index_bases
(
    criterion_id String,
    region_id String,
    act String,
    clause String,
    edition_date String,
    source_url String,
    unit String,
    thresholds Array(Float64),
    definition_sha256 String,
    currentness String,
    updated_at DateTime64(3,'UTC')
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (criterion_id,region_id);

ALTER TABLE plexus_normative.index_bases ADD COLUMN IF NOT EXISTS required_mode String DEFAULT 'car';
ALTER TABLE plexus_normative.index_bases ADD COLUMN IF NOT EXISTS regulation String DEFAULT 'threshold';

ALTER TABLE plexus_normative.index_bases ADD COLUMN IF NOT EXISTS review String DEFAULT '';
ALTER TABLE plexus_normative.index_bases ADD COLUMN IF NOT EXISTS intervals String DEFAULT '[]';
ALTER TABLE plexus_normative.index_bases ADD COLUMN IF NOT EXISTS required_measurement_definition String DEFAULT 'single_reference_point';
