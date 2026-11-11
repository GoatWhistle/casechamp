---
name: economic-assessment
description: Evaluate a saved closure's time cost, appraise a transport project, or explain regional economic indicators.
---

# Economic effects

Choose the branch from the conversation. Lead with the calculated effect, then
its assumptions and scope. Reuse known inputs; ask only for a missing required
input. Assumptions require the user's authorization and an explicit label.

## Saved settlement closure

Take the exact `connectivity-...` ID from displayed history and call:

```json
{"request":{"kind":"connectivity_economics","calculation_id":"<saved ID>","value_of_pcu_hour_rub":500}}
```

500 RUB/PCU-hour is an illustrative composite rate, not an observed price or wage.
Use a supplied rate instead. The tool reads the saved traffic scenario and computes
its cost. If traffic was not modeled, load `settlement-connectivity` and calculate
an authorized traffic scenario first. Use `recent` only to recover a missing ID
by matching places and closure; use `status` for inspection, not resubmission.

Report the rate, utilization and duration alongside the amount. The result covers
transit-cohort time, excluding background users, fuel and cargo value. Each pair
is independent; amounts cannot be summed. Null means incomplete, not zero.
PCU is a vehicle-equivalent unit, not passenger count. This is conditional time
cost, not total bridge damage, revenue or GDP/GRP loss.

## Regional transport project

Read the matching completed job with `manage_calculation(kind=status)` and use its
`appraisal_assumptions` and `appraisal_result`. Find a missing ID via `recent`.
Pending jobs have no final result. For a new intervention, load its road or rail/air
skill and submit it with `appraisal`; inspect capabilities if support is unclear.

Passenger inputs: explicit OD trips/year and RUB/person-hour, with provenance.
Freight: supplied or road-routed OD time/distance and rates. Population, company
revenue and hourly road traffic do not determine these OD inputs. Rail/air edits
do not model freight or truck restrictions. Missing route evidence is incomplete.

Project inputs: capital cost, annual incremental maintenance, horizon, real discount
rate, price year and provenance. Report calculated annual benefit, NPV, BCR and
discounted public-benefit payback; preserve signed losses. Payback is not investor
cash recovery. Low/base/high factors are scenarios, not confidence intervals.

## Regional business indicators

Use atlas economy and `query_atlas(kind=sources)`. Revenue means reported turnover
of covered companies; company counts can have different coverage. GDP/GRP needs
compatible official aggregates and periods. State coverage with the result.
