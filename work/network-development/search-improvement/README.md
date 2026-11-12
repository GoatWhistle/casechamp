# Search selection improvements, 2026-11-12

Authorized: improve mandatory CatBoost ranking, remove redundant verification, seed
from network problems, evaluate complementary packages, retain exact observations.
No independent speed changes. Generation120s and verification300s; preparation is
outside those windows. No search or retraining continues after the response.

Baseline is the completed `../llm-pilot-local-diff` run:19 exact index evaluations,
2 routed LLM hypotheses positive, best weighted regional gain0.0011267324508565935.
Old artifact and manifest are copied here before retraining.

`ranking-before.json` replays19 completed projects, in original evaluation order,
through the old mandatory model. Its top1 is zero gain; besttop3=.00003732539449,
besttop5=.00004647591457, besttop10=.00037380472280. This selected pool is biased by
the old search, and may overlap new training geometry. It is a diagnostic replay,
not a geographic holdout or causal estimate of overall improvement.

`problem-target-smoke.json`: actual4420OD synthetic demand on the real pilot graph,
30s geographic generation,12 routed connections,4from new problem-route seeds.
64OD paths produced420proposals;107Dijkstra origins,1149eligible pairs. This proves
candidate exposure/geographic routing only, not index gains.

Root regression for observations initially failed with KeyError:on_evaluated;
backend now records every completed score and its metric, including negatives.
Persisted provenance already contains graph/demand source and surrogate identity.
Timeouts are not labelled as zero; no automatic background training.

Final acceptance: all focused/full checks, after-model ranking replay, then one
frozen120+300s LLM-inclusive pilot on the same source demand/geography. Compare best
verified gain and verification coverage honestly; simultaneous changes and machine
load mean a single run is not statistical superiority evidence.

## Integrated validation

499 backend unit tests,186 ETL traffic/index/geography/selection tests passed; Ruff and mypy324modules passed. Final conservative singleton-package key change reran dedup5tests. New feature schema20, modelSHA5994fce91e127e54a383fb5aa2b14df9555a65404a2885fd626abde2604c72dc. Replay19now19distinctpredictions; top1+.00025399627887, top3/top5best+.00030908695358, top10best+.00112673245086. Prediction feature/model work .129s on this replay versusold.003s; this extra cost is not exact verification.

Full frozen run now `../llm-pilot-selection-v2`, one arm withsaved11LLMhypotheses, samegeography/demand. Runtime source frozen until finish; no new paidcalls.

## Completed pilot

`../llm-pilot-selection-v2/result.json`: valid_run/source_and_geography_stable true.11verified/11positive/1timeout;9LLM-containing projects verified. Bestweightedgain.001164057845358 versusprior.001126732450857 (+3.3127% of gain, smallabsoluteeffect). Generation120.258s,verification300.619s,preparation89.386s. Lowercoverage11vs19, selectedheavierprojects.27incompatiblepairs rejected,0exactduplicates in thispool,308distinctprojects,bufferpeak6. No newpaidLLMrequests. Compactpublicevidence docs/results/network-search-selection.json.

Postpilot pureprojection removes storedtrainingobservations fromchat/API responses withoutchangingstorage or numeric pipeline. Threeadditional boundarytests coverfullreply,event,HTTPsubmit/list/get/cancel andunchangedprovenance.50integrationchecks passed beforethisprojection; final502backendunit/Ruff/mypy326passed. APIrestartedPID46288initially, supersededby46878afterlegacyfixbelow.

## Runtime legacy record repair

Initialrestarthealth/UI/regions200, buttraffic-jobsGET500: legacyTrafficScope lacksregions. Added red/green fixture through ClickHouseTrafficStore.load. Generic recorddecoder nowusesdeclared dataclassdefaults onlyformissingoptionalfields; missingrequiredfieldsstillraiseKeyError. No persistedrecordsrewritten. Final504backendunit/50integration/186ETLpassed,Ruff+mypy327passed. API8007PID46878,UI5187direct+proxyhealth/regions/history200.12legacyjobsloaded; trainingobservationsabsentfrompublichistory. Sourcefreezeended; no paidcalls, commits orpushes.
