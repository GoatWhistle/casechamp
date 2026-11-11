---
name: interpret-accessibility
description: Explain or compare regional accessibility indices, coverage, seasonal differences and transport dependence.
---

# Interpret accessibility

Read the relevant regions using `query_atlas(kind=regions)`, `query_atlas(kind=places)` and `query_atlas(kind=regions, metric=...)`.
Use their returned model/artifact versions and the requested season/network. For
scenario feasibility and current graph rules, read `query_atlas(kind=capabilities)`.
History can contain results from older models; do not treat them as current values.

Hansen measures potential access to the population of 180 market cities, discounted
by model travel time. The regional score is weighted by origin population. The
formula is `sum(M_j * exp(-ln(2) / 2 * t_ij))` on a fixed normalization scale.
Scores are index points, not percentages of transport quality or economic output.
Keep absolute point changes separate from relative percentage changes. Compare
regions within the same model and scale; 100 is a historical normalization anchor,
not necessarily the current national mean. Local population in a market city also
contributes, so a high score alone does not prove strong interregional connections.

Coverage is the fraction of the input population/settlements with a finite model
path to at least one market. Say "among the atlas input population" when reporting
100%. It does not certify complete road data, operating services or observed trips.
Distinguish unknown values, no model path and zero effect. Catalog link counts do
not measure passenger traffic or establish those links' contribution to the index.

When asked about transport dependence, use a relevant network-change scenario
through `rail-air-scenarios` or `road-scenarios`. State what was removed and the
model/scope of the comparison. A model-based loss is not observed economic damage.
