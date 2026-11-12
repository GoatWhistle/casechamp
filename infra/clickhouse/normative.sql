CREATE DATABASE IF NOT EXISTS plexus_normative;
CREATE TABLE IF NOT EXISTS plexus_normative.criteria (
 id String, service String, act String, clause String, source_url String,
 edition_date String, threshold Float64, unit String, mode String,
 territory String, legal_status String, verification_status String
) ENGINE=MergeTree ORDER BY id;
CREATE TABLE IF NOT EXISTS plexus_normative.facilities (
 id String, service String, name String, address String, source_url String,
 observed_at String, latitude Nullable(Float64), longitude Nullable(Float64),
 coordinate_source Nullable(String), coordinate_status String
) ENGINE=MergeTree ORDER BY (service,id);
CREATE TABLE IF NOT EXISTS plexus_normative.run_rows (
 run_id String, stage LowCardinality(String), id String, name String,
 population Nullable(Int64), latitude Nullable(Float64), longitude Nullable(Float64),
 facility_id Nullable(String), minutes Nullable(Float64), excess_minutes Nullable(Float64),
 state LowCardinality(String)
) ENGINE=MergeTree ORDER BY (run_id,stage,id);
CREATE TABLE IF NOT EXISTS plexus_normative.run_facilities (
 run_id String, id String, service String, name String, address String, source_url String,
 observed_at String, latitude Nullable(Float64), longitude Nullable(Float64),
 coordinate_source Nullable(String), coordinate_status String
) ENGINE=MergeTree ORDER BY (run_id,id);
CREATE TABLE IF NOT EXISTS plexus_normative.runs (
 id String, created_at DateTime64(3,'UTC'), criterion_id String, act String,
 clause String, edition_date String, threshold Float64, source_url String,
 graph_revision String, region String, closed_way_ids Array(Int64)
) ENGINE=MergeTree ORDER BY (created_at,id);
CREATE TABLE IF NOT EXISTS plexus_normative.run_criteria (
 run_id String, id String, service String, act String, clause String, source_url String,
 edition_date String, threshold Float64, unit String, mode String,
 territory String, legal_status String, verification_status String
) ENGINE=MergeTree ORDER BY run_id;
ALTER TABLE plexus_normative.run_rows ADD COLUMN IF NOT EXISTS distance_metres Nullable(Float64);
ALTER TABLE plexus_normative.run_rows ADD COLUMN IF NOT EXISTS uncertainty Array(String);
ALTER TABLE plexus_normative.run_rows ADD COLUMN IF NOT EXISTS routing_node Nullable(Int64);
ALTER TABLE plexus_normative.run_rows ADD COLUMN IF NOT EXISTS approach_metres Nullable(Float64);
ALTER TABLE plexus_normative.runs ADD COLUMN IF NOT EXISTS model_revision String DEFAULT 'unversioned';
ALTER TABLE plexus_normative.runs ADD COLUMN IF NOT EXISTS ignored_way_ids Array(Int64);

CREATE TABLE IF NOT EXISTS plexus_normative.territories (
 point_id String, municipality_type String, source_url String, verification_status String
) ENGINE=MergeTree ORDER BY point_id;
ALTER TABLE plexus_normative.run_rows ADD COLUMN IF NOT EXISTS threshold_minutes Nullable(Float64);
ALTER TABLE plexus_normative.run_rows ADD COLUMN IF NOT EXISTS territory_type Nullable(String);
ALTER TABLE plexus_normative.run_rows ADD COLUMN IF NOT EXISTS territory_source_url Nullable(String);

CREATE TABLE IF NOT EXISTS plexus_normative.settlement_types (
 point_id String, settlement_type String, source_url String, verification_status String
) ENGINE=MergeTree ORDER BY point_id;
ALTER TABLE plexus_normative.runs ADD COLUMN IF NOT EXISTS fire_speed_kmh Nullable(Float64);
ALTER TABLE plexus_normative.runs ADD COLUMN IF NOT EXISTS fire_assumption Nullable(String);

CREATE TABLE IF NOT EXISTS plexus_normative.walking_facts (
 origin_id String,
 service String,
 source_url String,
 observed_at String,
 population Nullable(Int64),
 population_group Nullable(String),
 population_group_verified Bool,
 facility_id Nullable(String),
 entrance_latitude Nullable(Float64),
 entrance_longitude Nullable(Float64),
 entrance_verified Bool,
 facts_verified Bool,
 legal_currentness_verified Bool,
 measurement_verified Bool,
 service_eligible Nullable(Bool),
 service_active Nullable(Bool),
 region_code Nullable(String),
 municipality_type Nullable(String),
 municipality_legal_id Nullable(String),
 settlement_legal_id Nullable(String),
 settlement_category Nullable(String),
 origin_kind Nullable(String),
 exception_800_applicable Nullable(Bool),
 exception_source_url Nullable(String),
 sanitary_project_case Nullable(String),
 regional_planning_scope Nullable(Bool),
 municipal_planning_scope Nullable(Bool),
 zones Array(String),
 zone_source_url Nullable(String),
 zone_version Nullable(String),
 zoning_complete Nullable(Bool),
 bus_scope Nullable(Bool),
 bus_active Nullable(Bool),
 bus_return_trip Nullable(Bool),
 bus_vehicle_verified Bool,
 bus_route_km Nullable(Float64),
 bus_approach_metres Nullable(Float64),
 regional_transport_km Nullable(Float64)
) ENGINE=MergeTree ORDER BY (service,origin_id);
CREATE TABLE IF NOT EXISTS plexus_normative.run_rule_sets (
 run_id String, id String,
 checks Array(Tuple(rule_id String, applicability String, threshold Nullable(Float64),
 unit String, measurement String, value Nullable(Float64), result String, reason String,
 source_url String, edition_date String, facts_source_url Nullable(String),
 facts_observed_at Nullable(String), candidate_thresholds Array(Float64)))
) ENGINE=MergeTree ORDER BY (run_id,id);
ALTER TABLE plexus_normative.run_rows ADD COLUMN IF NOT EXISTS rule_set_id Nullable(String);

CREATE TABLE IF NOT EXISTS plexus_normative.run_walking_facts (
 run_id String,
 origin_id String,
 service String,
 source_url String,
 observed_at String,
 population Nullable(Int64),
 population_group Nullable(String),
 population_group_verified Bool,
 facility_id Nullable(String),
 entrance_latitude Nullable(Float64),
 entrance_longitude Nullable(Float64),
 entrance_verified Bool,
 facts_verified Bool,
 legal_currentness_verified Bool,
 measurement_verified Bool,
 service_eligible Nullable(Bool),
 service_active Nullable(Bool),
 region_code Nullable(String),
 municipality_type Nullable(String),
 municipality_legal_id Nullable(String),
 settlement_legal_id Nullable(String),
 settlement_category Nullable(String),
 origin_kind Nullable(String),
 exception_800_applicable Nullable(Bool),
 exception_source_url Nullable(String),
 sanitary_project_case Nullable(String),
 regional_planning_scope Nullable(Bool),
 municipal_planning_scope Nullable(Bool),
 zones Array(String),
 zone_source_url Nullable(String),
 zone_version Nullable(String),
 zoning_complete Nullable(Bool),
 bus_scope Nullable(Bool),
 bus_active Nullable(Bool),
 bus_return_trip Nullable(Bool),
 bus_vehicle_verified Bool,
 bus_route_km Nullable(Float64),
 bus_approach_metres Nullable(Float64),
 regional_transport_km Nullable(Float64)
) ENGINE=MergeTree ORDER BY (run_id,service,origin_id);

ALTER TABLE plexus_normative.walking_facts ADD COLUMN IF NOT EXISTS eligible_facility_ids Array(String);
ALTER TABLE plexus_normative.walking_facts ADD COLUMN IF NOT EXISTS eligible_inventory_complete Bool;
ALTER TABLE plexus_normative.run_walking_facts ADD COLUMN IF NOT EXISTS eligible_facility_ids Array(String);
ALTER TABLE plexus_normative.run_walking_facts ADD COLUMN IF NOT EXISTS eligible_inventory_complete Bool;

ALTER TABLE plexus_normative.walking_facts ADD COLUMN IF NOT EXISTS scenario_verified Bool;
ALTER TABLE plexus_normative.walking_facts ADD COLUMN IF NOT EXISTS verified_closed_way_ids Array(Int64);
ALTER TABLE plexus_normative.run_walking_facts ADD COLUMN IF NOT EXISTS scenario_verified Bool;
ALTER TABLE plexus_normative.run_walking_facts ADD COLUMN IF NOT EXISTS verified_closed_way_ids Array(Int64);

ALTER TABLE plexus_normative.walking_facts ADD COLUMN IF NOT EXISTS measurement_graph_revision Nullable(String);
ALTER TABLE plexus_normative.run_walking_facts ADD COLUMN IF NOT EXISTS measurement_graph_revision Nullable(String);

ALTER TABLE plexus_normative.facilities ADD COLUMN IF NOT EXISTS published_on Nullable(String);
ALTER TABLE plexus_normative.run_facilities ADD COLUMN IF NOT EXISTS published_on Nullable(String);

ALTER TABLE plexus_normative.territories ADD COLUMN IF NOT EXISTS municipality_code Nullable(String);
ALTER TABLE plexus_normative.territories ADD COLUMN IF NOT EXISTS structure_source_url Nullable(String);
ALTER TABLE plexus_normative.run_rows ADD COLUMN IF NOT EXISTS territory_verification_status Nullable(String);
ALTER TABLE plexus_normative.run_rows ADD COLUMN IF NOT EXISTS municipality_code Nullable(String);
ALTER TABLE plexus_normative.run_rows ADD COLUMN IF NOT EXISTS territory_structure_source_url Nullable(String);

CREATE TABLE IF NOT EXISTS plexus_normative.library_facts (
 origin_id String, source_url String, observed_at String, valid_from String, valid_until String,
 facts_verified Bool, legal_currentness_verified Bool, normative_source_url Nullable(String),
 legal_edition_date Nullable(String), jurisdiction_verified Bool, territory Nullable(String),
 municipality_type Nullable(String), municipality_code Nullable(String), planning_scope Nullable(Bool),
 population_verified Bool, population Nullable(Int64), population_reference Nullable(String),
 origin_reference_verified Bool, origin_latitude Nullable(Float64), origin_longitude Nullable(Float64),
 routing_node Nullable(Int64), approach_metres Nullable(Float64), measurement_verified Bool,
 measurement_graph_revision Nullable(String), transport_method_verified Bool, transport_mode Nullable(String),
 eligible_facility_ids Array(String), eligible_inventory_complete Bool, service_eligible Nullable(Bool),
 service_active Nullable(Bool), scenario_verified Bool, verified_closed_way_ids Array(Int64)
) ENGINE=MergeTree ORDER BY origin_id;
CREATE TABLE IF NOT EXISTS plexus_normative.run_library_facts (
 run_id String, origin_id String, source_url String, observed_at String, valid_from String, valid_until String,
 facts_verified Bool, legal_currentness_verified Bool, normative_source_url Nullable(String),
 legal_edition_date Nullable(String), jurisdiction_verified Bool, territory Nullable(String),
 municipality_type Nullable(String), municipality_code Nullable(String), planning_scope Nullable(Bool),
 population_verified Bool, population Nullable(Int64), population_reference Nullable(String),
 origin_reference_verified Bool, origin_latitude Nullable(Float64), origin_longitude Nullable(Float64),
 routing_node Nullable(Int64), approach_metres Nullable(Float64), measurement_verified Bool,
 measurement_graph_revision Nullable(String), transport_method_verified Bool, transport_mode Nullable(String),
 eligible_facility_ids Array(String), eligible_inventory_complete Bool, service_eligible Nullable(Bool),
 service_active Nullable(Bool), scenario_verified Bool, verified_closed_way_ids Array(Int64)
) ENGINE=MergeTree ORDER BY (run_id,origin_id);
ALTER TABLE plexus_normative.run_rows ADD COLUMN IF NOT EXISTS qualification_source_url Nullable(String);
ALTER TABLE plexus_normative.run_rows ADD COLUMN IF NOT EXISTS qualification_observed_at Nullable(String);
ALTER TABLE plexus_normative.runs ADD COLUMN IF NOT EXISTS qualification_as_of Nullable(DateTime64(3,'UTC'));

CREATE TABLE IF NOT EXISTS plexus_normative.medical_facts (
 origin_id String, source_url String, observed_at String, valid_from String, valid_until String,
 service String, population_group Nullable(String), ownership_scope_verified Bool,
 ownership_applicable Nullable(Bool), facility_form_verified Bool, adult_profile_verified Bool,
 catchment_verified Bool, catchment_source_url Nullable(String), regional_adjustment_verified Bool,
 regional_adjustment_source_url Nullable(String), threshold_minutes Nullable(Float64),
 facts_verified Bool, legal_currentness_verified Bool, normative_source_url Nullable(String),
 legal_edition_date Nullable(String), jurisdiction_verified Bool, territory Nullable(String),
 planning_scope Nullable(Bool),
 population_verified Bool, population Nullable(Int64), population_reference Nullable(String),
 origin_reference_verified Bool, origin_latitude Nullable(Float64), origin_longitude Nullable(Float64),
 routing_node Nullable(Int64), approach_metres Nullable(Float64), measurement_verified Bool,
 measurement_graph_revision Nullable(String), transport_method_verified Bool, transport_mode Nullable(String),
 eligible_facility_ids Array(String), eligible_inventory_complete Bool, service_eligible Nullable(Bool),
 service_active Nullable(Bool), scenario_verified Bool, verified_closed_way_ids Array(Int64)
) ENGINE=MergeTree ORDER BY (service,origin_id);
CREATE TABLE IF NOT EXISTS plexus_normative.run_medical_facts (
 run_id String, origin_id String, source_url String, observed_at String, valid_from String, valid_until String,
 service String, population_group Nullable(String), ownership_scope_verified Bool,
 ownership_applicable Nullable(Bool), facility_form_verified Bool, adult_profile_verified Bool,
 catchment_verified Bool, catchment_source_url Nullable(String), regional_adjustment_verified Bool,
 regional_adjustment_source_url Nullable(String), threshold_minutes Nullable(Float64),
 facts_verified Bool, legal_currentness_verified Bool, normative_source_url Nullable(String),
 legal_edition_date Nullable(String), jurisdiction_verified Bool, territory Nullable(String),
 planning_scope Nullable(Bool),
 population_verified Bool, population Nullable(Int64), population_reference Nullable(String),
 origin_reference_verified Bool, origin_latitude Nullable(Float64), origin_longitude Nullable(Float64),
 routing_node Nullable(Int64), approach_metres Nullable(Float64), measurement_verified Bool,
 measurement_graph_revision Nullable(String), transport_method_verified Bool, transport_mode Nullable(String),
 eligible_facility_ids Array(String), eligible_inventory_complete Bool, service_eligible Nullable(Bool),
 service_active Nullable(Bool), scenario_verified Bool, verified_closed_way_ids Array(Int64)
) ENGINE=MergeTree ORDER BY (run_id,service,origin_id);

ALTER TABLE plexus_normative.run_rows ADD COLUMN IF NOT EXISTS catchment_source_url Nullable(String);
ALTER TABLE plexus_normative.run_rows ADD COLUMN IF NOT EXISTS threshold_source_url Nullable(String);

ALTER TABLE plexus_normative.facilities ADD COLUMN IF NOT EXISTS source_sha256 Nullable(String);
ALTER TABLE plexus_normative.run_facilities ADD COLUMN IF NOT EXISTS source_sha256 Nullable(String);

ALTER TABLE plexus_normative.facilities ADD COLUMN IF NOT EXISTS coordinate_snapshot_sha256 Nullable(String);
ALTER TABLE plexus_normative.facilities ADD COLUMN IF NOT EXISTS coordinate_snapshot_url Nullable(String);
ALTER TABLE plexus_normative.run_facilities ADD COLUMN IF NOT EXISTS coordinate_snapshot_sha256 Nullable(String);
ALTER TABLE plexus_normative.run_facilities ADD COLUMN IF NOT EXISTS coordinate_snapshot_url Nullable(String);
