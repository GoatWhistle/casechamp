---
name: economic-assessment
description: Assess economic effects of transport changes, project costs and benefits, or answer questions about regional economic contribution.
---

# Assess economic effects

Resolve what "economic contribution" refers to using the user's question and recent
context. A transport discussion calls for the effect of a specific change, rather
than silently substituting company revenue. If the user explicitly asks about the
size of regional business, use the atlas economy and `query_atlas(kind=sources)`. Company revenue is
reported turnover in the covered company sample; company count and revenue may
have different coverage. Neither is regional value added, GDP share or transport
benefit. A GDP/GRP contribution needs compatible official aggregates and periods;
those are not supplied by a company-revenue total.

For a transport effect, inspect `query_atlas(kind=capabilities)` and relevant saved jobs
with `manage_calculation(kind=recent)` / `manage_calculation(kind=status)`. Reuse a matching completed
job, including its `appraisal_assumptions` and `appraisal_result`; do not rerun it
or substitute today's atlas index for its recorded baseline. Pending jobs have no
final result. If the user asks to evaluate a new intervention, load the corresponding
road or rail/air skill and submit it with an optional `appraisal`.

Passenger appraisal needs explicit origin-to-market trips/year, rubles/person-hour
and a source/period or labelled user assumption. Time before/after comes from the
graph for each supplied pair, including transit beneficiaries. Freight can use
explicit times/km or road-routed OD inputs; rail/air changes do not model rail/air
cargo or truck restrictions. Do not derive OD demand from residents, company
revenue or hourly road traffic. Values of time monetize saved time, not actual
cash receipts. Missing route evidence makes the aggregate incomplete, not zero.

Project evaluation also needs capital cost, annual incremental maintenance, horizon,
real discount rate, price year and cost provenance. Low/base/high demand and value
factors are explicit assumptions, not confidence intervals. Preserve signed losses.
Use the calculated annual benefit, net benefit, NPV, benefit/cost ratio and discounted
public-benefit payback where available. Do not present that payback as investor
cash recovery. Check costs even when the index improves.

Lead with the requested conclusion and its basis. If inputs are missing, name the
specific missing intervention/flows/rates/costs in one concise question and explain
what can already be calculated, such as the index effect without rubles. Use known
conversation inputs; do not ask the user to repeat them. Do not invent assumptions
unless the user requests an illustrative calculation; label those explicitly.
Keep broader GDP, induced demand and fiscal claims outside this conditional model.

For a selected-settlement closure, a `connectivity-...` ID in displayed table
history identifies its durable calculation. Prefer that exact ID over a global
recent listing. `manage_calculation(kind=connectivity_economics, calculation_id=...,
value_of_pcu_hour_rub=500)` computes from its SAVED traffic result. The default rate
is illustrative, not measured: use it only when the user authorizes assumptions,
and state the rate, utilization and duration. If traffic was not modeled, load
settlement-connectivity and calculate it with explicit traffic assumptions before
monetizing. Do not claim missing traffic when the saved result includes modeled
traffic. Do not convert PCU to passengers or trucks without additional evidence.
Report each pair independently; these corridor experiments overlap and cannot be
summed. The monetary result excludes background users, freight value and fuel.
