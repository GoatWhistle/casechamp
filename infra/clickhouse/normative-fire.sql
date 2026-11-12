CREATE TABLE IF NOT EXISTS plexus_normative.fire_facts (
 origin_id String, source_url String, observed_at String, valid_from String, valid_until String,
 settlement_type_verified Bool, settlement_type Nullable(String), speed_verified Bool,
 speed_kmh Nullable(Float64), speed_source_url Nullable(String), profile_assumption Nullable(String),
 adverse_conditions_verified Bool, vehicle_access_verified Bool, directionality_verified Bool,
 operational_readiness_verified Bool, destination_objects_verified Bool, population_scope Nullable(String),
 measurement_definition_verified Bool, measurement_definition Nullable(String), method_source_url Nullable(String), method_currentness_verified Bool, method_edition_date Nullable(String),
 facts_verified Bool, legal_currentness_verified Bool, normative_source_url Nullable(String),
 legal_edition_date Nullable(String), jurisdiction_verified Bool, territory Nullable(String),
 planning_scope Nullable(Bool),
 population_verified Bool, population Nullable(Int64), population_reference Nullable(String),
 origin_reference_verified Bool, origin_latitude Nullable(Float64), origin_longitude Nullable(Float64),
 routing_node Nullable(Int64), approach_metres Nullable(Float64), measurement_verified Bool,
 measurement_graph_revision Nullable(String), transport_method_verified Bool, transport_mode Nullable(String),
 eligible_facility_ids Array(String), eligible_inventory_complete Bool, service_eligible Nullable(Bool),
 service_active Nullable(Bool), scenario_verified Bool, verified_closed_way_ids Array(Int64)
) ENGINE=MergeTree ORDER BY origin_id;
CREATE TABLE IF NOT EXISTS plexus_normative.run_fire_facts (
 run_id String, origin_id String, source_url String, observed_at String, valid_from String, valid_until String,
 settlement_type_verified Bool, settlement_type Nullable(String), speed_verified Bool,
 speed_kmh Nullable(Float64), speed_source_url Nullable(String), profile_assumption Nullable(String),
 adverse_conditions_verified Bool, vehicle_access_verified Bool, directionality_verified Bool,
 operational_readiness_verified Bool, destination_objects_verified Bool, population_scope Nullable(String),
 measurement_definition_verified Bool, measurement_definition Nullable(String), method_source_url Nullable(String), method_currentness_verified Bool, method_edition_date Nullable(String),
 facts_verified Bool, legal_currentness_verified Bool, normative_source_url Nullable(String),
 legal_edition_date Nullable(String), jurisdiction_verified Bool, territory Nullable(String),
 planning_scope Nullable(Bool),
 population_verified Bool, population Nullable(Int64), population_reference Nullable(String),
 origin_reference_verified Bool, origin_latitude Nullable(Float64), origin_longitude Nullable(Float64),
 routing_node Nullable(Int64), approach_metres Nullable(Float64), measurement_verified Bool,
 measurement_graph_revision Nullable(String), transport_method_verified Bool, transport_mode Nullable(String),
 eligible_facility_ids Array(String), eligible_inventory_complete Bool, service_eligible Nullable(Bool),
 service_active Nullable(Bool), scenario_verified Bool, verified_closed_way_ids Array(Int64)
) ENGINE=MergeTree ORDER BY (run_id,origin_id);
ALTER TABLE plexus_normative.run_rows ADD COLUMN IF NOT EXISTS travel_profile_source_url Nullable(String);
ALTER TABLE plexus_normative.run_rows ADD COLUMN IF NOT EXISTS measurement_method_source_url Nullable(String);
ALTER TABLE plexus_normative.fire_facts ADD COLUMN IF NOT EXISTS method_currentness_verified Bool;
ALTER TABLE plexus_normative.fire_facts ADD COLUMN IF NOT EXISTS method_edition_date Nullable(String);
ALTER TABLE plexus_normative.run_fire_facts ADD COLUMN IF NOT EXISTS method_currentness_verified Bool;
ALTER TABLE plexus_normative.run_fire_facts ADD COLUMN IF NOT EXISTS method_edition_date Nullable(String);
CREATE TABLE IF NOT EXISTS plexus_normative.fire_destinations (
 id String,name String,address String,region String,latitude Float64,longitude Float64,
 source_url String,observed_at String,reference_status String,source_sha256 Nullable(String)
) ENGINE=MergeTree ORDER BY (region,id);
CREATE TABLE IF NOT EXISTS plexus_normative.run_fire_destinations (
 run_id String,id String,name String,address String,region String,latitude Float64,longitude Float64,
 source_url String,observed_at String,reference_status String,source_sha256 Nullable(String)
) ENGINE=MergeTree ORDER BY (run_id,id);
ALTER TABLE plexus_normative.fire_facts ADD COLUMN IF NOT EXISTS population_partition_verified Bool;
ALTER TABLE plexus_normative.run_fire_facts ADD COLUMN IF NOT EXISTS population_partition_verified Bool;
ALTER TABLE plexus_normative.run_rows ADD COLUMN IF NOT EXISTS origin_source_url Nullable(String);
ALTER TABLE plexus_normative.run_rows ADD COLUMN IF NOT EXISTS origin_observed_at Nullable(String);
ALTER TABLE plexus_normative.run_rows ADD COLUMN IF NOT EXISTS origin_source_sha256 Nullable(String);
ALTER TABLE plexus_normative.run_rows ADD COLUMN IF NOT EXISTS origin_reference_status Nullable(String);
ALTER TABLE plexus_normative.runs ADD COLUMN IF NOT EXISTS origin_basis Nullable(String);
