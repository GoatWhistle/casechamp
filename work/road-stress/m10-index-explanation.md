# M-10 regional index explanation, 2026-11-11

User asks why the714-way closure only changes Novgorod Hansen84.1449to82.1432.
Read-only inspection; no new calculations, model calls or code changes.

Exact saved job on API8007:70e7cc24c01d4682bd05bfb97fc0bcd0, scenario road,
version road-8033092fca2cf5fa,714ways/1534edges. Before84.14492901924532,
after82.14323499393292, delta-2.0016940253124034,
relative_percent-2.3788647143009434, regional population583387.

Matching road-only national stress job95c3a442bf544d118fac5403cf80eede already exists;
its way ID set equals the regional job exactly. All96newly isolated points are in:
- Novgorod:3713affected points,64newly without any external model market,
  population1414, maximum finite directional delay207.30689683870878minutes.
- Tver:8834affected points,32newly without any external model market,
  population3974, maximum finite directional delay162.95670449675526minutes.
1414/583387=0.2423777012514849% of the Novgorod population weight.
These are snapshot reachability results, not verified physical isolation/traffic.

Legacy regional formula: population-weighted sum of180market populations with
exponential2hour half-life, fixed country-baseline normalization=100. Includes self
market; regional average can conceal severe local losses. Other network alternatives
remain. No traffic redirection/congestion was calculated in these saved jobs.

Active ClickHouse metadata has road_cost_model_version=road-capacity-v1 but no
model_version row. GraphData.modern_model therefore false; GraphRouting.networks('road')
loads intercity rail/air. Source table has28056rail/6618air records with time.
Thus this regional result is NOT equivalent to a road-only freight stress test.
No attribution of the2.38% loss to particular modes/markets was computed; do not claim
an exact numerical decomposition or that the number independently validates the model.

The pasted card is legacy Hansen, but do not claim national stress was never run:
the exact matching completed national job was found on8007 (8817's memory lacks it).
