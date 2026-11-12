CREATE TABLE IF NOT EXISTS plexus_normative.regional_measurements_rows AS plexus_normative.run_rows;
ALTER TABLE plexus_normative.regional_measurements_rows ADD COLUMN IF NOT EXISTS position UInt32;
CREATE TABLE IF NOT EXISTS plexus_normative.regional_measurements_facilities AS plexus_normative.run_facilities;
ALTER TABLE plexus_normative.regional_measurements_facilities ADD COLUMN IF NOT EXISTS position UInt32;
ALTER TABLE plexus_normative.regional_measurements ADD COLUMN IF NOT EXISTS measurement_definition String DEFAULT 'single_reference_point';
