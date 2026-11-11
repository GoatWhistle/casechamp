# Proposed hackathon decision scenario

## Further clarification: trip purpose before economic effects

The user supplied the following clarification after the screenshot. Attribution is
unconfirmed; this is preserved user-provided guidance, not a new official regulation.

> Прирост выручки хорош все же как экономическая метрика сама по себе 
>
> но сам по себе он ещё не показывает качество транспортных связей — такое может быть скорее где то частью индекса 
>
> выручка может вырасти из-за повышения цен или спроса, даже если перевозить стало дольше и сложнее
>
> в случае с маркетплейсом пример про выбор показателя под задачу. в вашем кейсе предмет уже задан: оценить, насколько транспортные связи подходят для выбранных поездок или перевозок. а конкретного пользователя и его потребность вы определяете сами
>
> ну вот самый банальный индекс это среднее время, за которое жители могут добраться до ближайшей школы по доступным маршрутам

Planning consequence: name the trips and destination selection explicitly before choosing
the main indicator. A general promise to assess network quality or help management is
insufficient. The school example explains the principle; it does not request school data
or change the product into education-access analysis. Revenue growth is not implemented
and remains outside the transport-quality score and causal claims.

For the worked example, use residents' modeled automobile trips from selected settlements
to one explicitly named common center. Keep directions and population scope fixed across
variants. Expose actual time and path availability beside any transformed score. Do not
claim the center's employment, healthcare or educational opportunities without those data.
The regional planner's intervention decision and the common experiment remain proposed.
Do not silently replace Hansen or add an unvalidated composite. If reporting a mean time,
show unreachable/unbound directions separately; excluding them after a closure must not
produce an apparent improvement. Pair score zero for no path is not zero travel time.

Next specification must answer: whose trip, from where, to which destination(s), by what
transport, under which conditions, and what observable improvement matters. No code change
or fresh validation is implied by this clarification.

## Revised framing after the consultation screenshot

The user's follow-up screenshot clarifies the task's center: choose and justify metrics
that let a decision-maker evaluate transport-network quality. The marketplace analyst
is an analogy, not a requirement to serve marketplaces. Source: `brief/QA.md`, received
2026-11-11; speaker identity and message date are not visible.

This revision supersedes the primary framing below that made a small-group center-access
score the main product. Retain that calculation as route-level diagnosis and the closure
experiment as a worked application. Do not remove the regional atlas or silently change
its score. Everything here remains a proposal, not an approved implementation.

Primary user: a regional transport-planning analyst preparing infrastructure priorities
for management. Decision: which accessibility problem and which candidate intervention
deserve detailed engineering/cost assessment first.

Primary purpose: evaluate potential access to the population of model market cities,
its vulnerability to specified network disruptions, and improvement from specific projects.
The central questions are access now, access lost under a specified disruption, and access
recovered/improved by an intervention. Use the same underlying accessibility measure for
scenario deltas; no new weighted composite or claim of universal network quality.

Hansen remains the regional overview. Define exactly which market opportunities, origin
population, network, season, normalization and graph snapshot it uses. High means greater
time-discounted access to these markets; low means less. 100 is a normalization anchor,
not perfect transport or a percentage. Own-market contribution must be decomposed before
interpreting the number as external connectivity; if an external-only view is introduced,
version and recompute it consistently rather than relabeling historical values.

Revised P0 order:
1. Publish one metric/decision specification: user, purpose, scale, inputs, formula, units,
   score direction, role of own-market contribution and an example decision.
2. Present three linked views: current access, loss under a named disruption, and intervention
   effect. Attach named routes, disconnected places, comparable times and exposed residents.
   Treat vulnerability as specific to the tested disruption, not general reliability.
3. Finish the common experiment contract and scenario inheritance described below. Compare
   open baseline, disruption, disruption plus A/B on unchanged origin/destination scope.
   Pair time and regional Hansen comparisons must declare their different network scopes;
   use consistent scope within each before/after comparison.
4. Give the agent these facts through existing tools, including market-contribution evidence,
   and require calculation-backed comparison and tradeoffs. Avoid unsupported investment
   or logistics-demand recommendations.
5. Validate score behavior and a real case: closures cannot improve fixed-network access,
   ineffective interventions can return zero, local losses remain visible under averages,
   parameter sensitivity is reported, and independent route checks support the explanation.
6. Demonstrate the regional comparison, drill into one corridor, evaluate two interventions,
   and end with a supported priority. Keep the saved-result fallback and explicit AI checks.

The main remaining gap is a justified, interpretable decision system around existing
calculators. More stored indices, broad new data collection and a national traffic model
are not prerequisites. Existing engineering tasks below remain candidate work items,
but the selected-group score is no longer proposed as the primary regional metric.

## Earlier proposal and preserved user guidance

2026-11-11. Planning only, not an approved implementation or measured product claim.
Branch `feat/map-first-ui`, HEAD `cdb2c2e1108bde7ff37ab91f9d7907d05de2a897`.
Applied `hack-kickoff` and `jury-route` to the current task and capability review.
No product changes, paid calls, fresh calculations, deployment or submission.

## User guidance, verbatim

тепереь сформулируй что нужно доделать чтобы закрыть это для вау эффекта на хакатон. Пользователя и назначение индекса вы определяете сами и ак следствие от этого зависит, что именно он должен показывать

тут как и с любым продуктом важно сформулировать: кто смотрит на вашу оценку и какое решение принимает с её помощью


Индекс может описывать связь двух территорий или положение одной территории относительно других. Все тут зависит от постановки задачи. Возможна и оценка всей рассматриваемой сети (опять же какого уровня сами решаете)

выбираете масштаб под свою задачу и формулируете как следствие, что означают высокие и низкие значения и что с ними можно придумать потом

несколько индексов допустимы, в том числе для разных видов перевозок или грузов. главное всеж понимать смысл каждого показателя и точно не зарыться в какое то чрезмерное количество допущений и тд

с дорогами да, но в таком случае важно объяснить, что стоит за изменением индекса. доставка становится дольше или часть направлений теряет доступность или исчезает запасной путь? И какое решение помогает принять этот результат


по сути ваш результат тут это понятный и обоснованный инструмент оценки транспортных связей 

и его пользу вы показываете на конкретных примерах: что он позволяет заметить, сравнить и решить (и кому)

Attribution/date of the quoted consultation beyond this user message are unconfirmed.
Do not invent an organizer identity or change official source precedence.

## Proposed product choice

Primary user: a regional transport-planning analyst preparing a shortlist of reserve-road
improvements for detailed engineering assessment.
Decision: which of two specified alternative-road improvements better preserves automobile
access from selected settlements to a shared service center during a defined road closure.
No assertion of real traffic demand, hospital access, truck feasibility or investment returns.

Scale: one real corridor, 4–6 named places including the center, with the same origin-center
pairs in every variant. Compare settlements as territories, then compare interventions.
The national atlas provides context and replication potential, not the main demonstration.

Hypothesis: useful connectivity means short model trips and retained access when a selected
road fails. A larger score can hide a lost connection, so missing paths remain separate.
Use existing selected-settlement score, `100 * 2**(-hours/2)`, equally averaged across
origin-center pairs. Two hours gives 50, four hours 25; two hours is a chosen time scale,
not a calibrated behavioral or regulatory threshold. No-path pairs score zero and remain
in the average; absent graph attachment makes the group result unknown.
Compare only identical pair sets/weights/graph versions. Residents are exposure context,
not trip volumes. Retain regional Hansen as a separate macro view, with its own-market
contribution and active transport modes clearly described.

## P0 work and acceptance

1. Record the user, decision, scale, hypothesis and score meaning consistently in product
   purpose, methodology, passport and defense. Replace relevant product placeholders.
   Acceptance: one named role and decision; no conflicting definitions. R01–R06, R13.
2. Add one experiment contract: open baseline, closure, same closure plus alternative A,
   same closure plus alternative B. Exact interventions and pair set are persisted.
   Existing generic road scenarios support combined road changes, but selected-group
   connectivity needs support for those profile changes/additions and shared comparison.
   Current `edit_selection` starts from the OPEN network and must not be used as if it
   inherited a closure. Prefer two existing reserve-road speed/profile improvements for
   P0; hypothetical new connections add engineering assumptions. R08–R09.
3. Produce comparable per-pair time, path status and geometry for all variants. Show
   group score, disconnected pairs, worst travel time and residents of relevant places.
   Distinguish improvement versus the closure from residual loss versus open baseline.
   Unknown times must not become zeros. No summing infinite times. R05–R10, R14.
4. Build one compact comparison view and map. Selected closure, original routes and
   alternative routes have clear names; choosing a settlement highlights its pair.
   New fields flow through existing unified tools and server-rendered tables. No model-
   supplied numerical cells, new forest of tool names or guaranteed invented conclusions.
   Acceptance: user can trace each claimed effect to a row and route. R10, R12, R14.
5. Teach agent to compare completed variants on the fixed scope, identify actual tradeoffs,
   and propose a candidate for further assessment. A dominates B only if returned metrics
   support it; ties/conflicts must remain explicit. Without comparable project costs,
   this is an accessibility choice, not economic optimality. R10–R13.
6. Fix a validation plan before runs, then validate one real corridor and both alternatives.
   Inspect the chosen roads/attachments; check closure monotonicity, unchanged pair set,
   no benefit from an unrelated edit, null/no-path handling, persisted results and source
   preservation. Check parameter sensitivity (proposed half-lives 1/2/4 hours); report a
   changed ranking if found. No guarantee that a chosen improvement helps. R04–R11.
7. Evaluate the free-text agent only with explicit authorization for model calls. Proposed
   small benchmark: ten documented requests spanning find/closure/variants/follow-up,
   ambiguity, missing inputs, nulls and no-effect scenarios. Check actual tool selection,
   scenario inheritance and every quoted numerical fact; record failures. Unit tests from
   the capability review are not evidence of this behavior. R12, R18.
8. Prepare a live route, saved-result fallback and short backup recording. Precomputed runs
   are labeled as saved, with actual runtime available. The UI supports the main calculation
   without an LLM. Defense: user/problem, score/data, baseline failure, alternative comparison,
   supported decision/checks, limits/roadmap. 5–8 slides and <=5 minutes per brief. R17–R18.

P0 completion means one complete, checked decision case, not a count of new features.
No published criterion weights; prioritize the currently weakest connection to the problem.

## Demonstration outline (proposed)

1. Identify the analyst's decision and show selected settlements plus common center.
2. Compare baseline pair scores/times; explain the time scale with one concrete route.
3. Close the exact bridge/road and show named lost or delayed connections.
4. Compare two specified reserve-road improvements, retaining the same closure.
5. Inspect a route and a numerical row supporting the tradeoff or preferred candidate.
6. Show a negative/no-effect/ambiguous case and how the tool avoids an unsupported claim.
7. Give the decision supported by the evidence and what engineering/cost evidence remains.

Use existing Stavropol-area bridge experiments as a candidate, not an already validated
selection. Verify that relevant places and two meaningful reserve-road interventions exist
before fixing the demo. Preserve unsuccessful candidate evidence; do not manufacture a win.

## P1 and deferred scope

P1 after P0: optional modeled queues on the selected OD pairs; conditional costs with a
single visible assumption set; a short rail/air transferability example.
Do not imply that the existing traffic tool already supports improved-road experiment
variants; verify or implement that separately if included. Cross-pair flows are independent.

Defer broad exposure of every stored index, a full national OD traffic model, GDP/revenue
forecasts, new source campaigns and automatic investment optimization. These do not fix
the immediate decision gap. Real schedules, flow calibration, directional/truck restrictions
and engineering validation belong on the roadmap with explicit data dependencies.

## State and next action

This proposal narrows the main demonstration while preserving existing atlas capabilities.
No implementation is authorized by the request to formulate the work. Next, if requested,
fix the experiment schema and validate candidate geography before building the comparison.
External submission receipt and defense time remain unresolved in existing context.
No new runtime checks were necessary for this planning-only task.
