CREATE DATABASE IF NOT EXISTS plexus_normative;
CREATE TABLE IF NOT EXISTS plexus_normative.pedestrian_nodes (
 revision String, node_index UInt32, osm_id Int64, latitude Float64, longitude Float64
) ENGINE=MergeTree ORDER BY (revision,node_index);
CREATE TABLE IF NOT EXISTS plexus_normative.pedestrian_edges (
 revision String, way_id Int64, source UInt32, target UInt32, metres Float64
) ENGINE=MergeTree ORDER BY (revision,source,target,way_id);
CREATE TABLE IF NOT EXISTS plexus_normative.pedestrian_origins (
 revision String, id String, name String, latitude Float64, longitude Float64,
 coordinate_source String, origin_type LowCardinality(String)
) ENGINE=MergeTree ORDER BY (revision,id);
CREATE TABLE IF NOT EXISTS plexus_normative.pedestrian_networks (
 revision String, created_at DateTime64(3,'UTC'), source_url String,
 source_sha256 String, source_timestamp String, rules_version String,
 node_count UInt64, edge_count UInt64, origin_count UInt64,
 excluded_counts Map(String,UInt64)
) ENGINE=MergeTree ORDER BY (created_at,revision);
