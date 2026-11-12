# Network development implementation, 2026-11-12

Branch `feat/transport-scenarios-update`, source HEAD `5daf6815eac9105d5b4b74e7013a5a49a5faf2e3`.
Uncommitted work existed before this task and was preserved. No commit, push or server restart performed.
Three GPT-6.1 Sol workers used isolated detached worktrees in /private/tmp; root integrates explicitly owned files.

Implemented sole development path: mandatory packaged trained CatBoost, geography A*, incremental traffic routing,
index delta, bounded process search, compatible pairs, multi-region input, closure/opening types, same routed
geometry in model/map, overload increase in existing UI. Removed first-per-type three-project selector,
full candidate assignment in screening, straight housing-clearance path. Full solver remains a reference
for training and validation. CLI candidates calls the same search.

Primary method/limitations: ../../docs/network-development.md.

Evidence:
- Backend unit suite 460 passed before deletion of obsolete clearance test; mypy312 files passed.
- Backend integration50passed with .env.analytics against local ClickHouse; first attempts failed for
  missing environment then sandbox local-socket denial; approved rerun passed.
- Frontend verify passed:36rules,types,lint,502tests,build. Existing PostCSS/chunk-size warnings remain.
- ETL45tests passed (incremental, geography, search and legacy suite adapted to new contract).
- National index9differential tests compare current formula, snaps, virtual points, multi-link edits,
  closure and normalization. Disk-backed cache integrated and tested; ETL total48passed.
- pilot.json: real road snapshot11312edges/110OD,319candidate tasks processed in54.954seconds;
  generated31routedconnections. Includes invalid/unconverged rejections in processed count;
  separate verified/rejected counters added afterwards. Objective local accessibility, not national index.
- data/traffic-geography/geography.json+manifest.json: real Nevinnomyssk pilot raster121x131,
  OSM14655buildings,131waterfeatures,1protectedfeature and Copernicus GLO30 DSM.
- data/traffic-geography/actual-flow-smoke.json: optimized generator12nonstraight routes in~0.99s,
  2.9–17.25km,28–154vertices. Input11312edge identities matched stored flow baseline.
- etl/synthetic_traffic/surrogate.json:448train/174heldout labels including two real topologies with
  synthetic demand. Package ranking and national-index ranking not independently validated.

Runtime dependencies installed in backend/.venv; editable ETL import avoids PYTHONPATH=etl shadowing
stdlib graphlib with etl/graphlib.py. Do not set that PYTHONPATH for app startup.

Known limits: geography only pilot coverage; raster feasibility is not engineering survey; existing
road widening does not validate right-of-way. At most two-project packages. Source export has2million
edge/home safety limits and128zones. External transit remains omitted in clipped demand; road index
uses national context. No nationwide end-to-end minute timing. National graph measured6,990,556nodes /
17,393,384edges: Python graph dictionaries/all-market trees in RAM are infeasible, compact disk-backed
index cache integrated, approximate15.1GB disk for180markets, sparse candidate overlays and cleanup. Baseline preparation is outside search timer. No paid LLM validation.

National cache smoke executed against real ClickHouse graph:17,560,380 symmetric CSR edges,
6,990,556nodes, one market. Warm tree read0.12s; changed tree edge repaired1node/1origin in2.10s.
Protocol national-cache-smoke.json. This is not a 180-market or national-search speed guarantee.
Full app first run correctly exposed current atlas is not marked hansen-frequency-v2; implementation
now preserves its legacy72h horizon and trunk-transfer formula as GraphRouting does. Added differential
regression test;10index tests pass. Full application run ongoing with all markets cached on disk.


Final scope, 2026-11-12: sole adaptive development tool supports connectivity/transit/congestion;
city-name residential focus, fixed baseline transit cohort, overload reporting. Removed exposed
legacy sensitivity/edit/raw-link paths and standalone speed interventions, including manual HTTP
speed overrides. Lane additions retained subject to raster footprint screening. No original
bridge/tunnel inventory means widening remains preliminary, not engineering clearance.
CatBoost retrained without speed projects:550train/209heldout,18/7groups; required artifact/hash.
Numba0.67 compiled local repair and72hlegacy pruning; no candidate full shortest-path recompute.
Candidate index verification has5second slice within60second search to avoid starvation.
Earlier national runs produced0verified gains, including60.08ssearch34verified/40processed.
Do not present earlier local speed-enabled gains as final evidence.
Final no-speed design-based localpilot:194processed in9.955s,32newlinks,32closures,2laneoptions
(62of64widenings rejected bygeography). Bestlocalaccess +0.0001270975%,0.008862748vehicle-hours/h
saved,3overloadededges unchanged. Realroadtopology/syntheticdemand110OD. NOT nationalindex gain.
Checks:backend472unit,Ruff,mypy314;50ClickHouseintegration;69ETLtests;frontend36rules,
typecheck/lint504tests/build passed before final removal of rawconnection UI/API.
Numba initialpin<0.64 conflicted withNumPy2.5; resolved withNumba0.67 official support:
https://numba.readthedocs.io/en/0.67.0/release/0.67.0-notes.html
Docker runtime now includeseditableETLsources andwritableNumba cache; Dockerimage notbuilt here.
No paidLLMcheck, no apprestart/deployment, no commit/push. Final regional-index repeat completed: 60.226s search,39processed/34verified,0positive alternatives;44.82s preparation,105.08s total. Full response under a minute is NOT achieved.

Final checks after rawconnection removal:472backendunit, Ruff/mypy314; frontend36rules/typecheck/lint/506tests/build;69ETL and50integration passed. Context budget passes with protected-instruction overflow; no instructions deleted. Next: broaden geographically supported corridor proposals and establish material regional-index gains; currentpilot didnotconfirm them. No standperformance claim.


## LLM hypotheses and geography expansion, 2026-11-12

Current work supersedes earlier no-paid-LLM notes: user explicitly requested a real LLM pilot.
Saved `llm-input.json` and `llm-hypotheses.json`: gpt-6.1-sol produced11place-pair
hypotheses in26.5146s,11066input/998output tokens. First paid call completed but
its response was lost on Decimal usage serialization; second call saved successfully.
No gains are established by generation alone. Manual A/B runner uses the same actual
ClickHouse index, frozen local graph/demand/geography and mandatory CatBoost;120s
generation +60s verification per arm, no standalone speed interventions.

Frozen pilot `data/traffic-geography-hypothesis-pilot/geography.npz` covers
[41.7,44.44,42.2,44.81],371×501cells;99.55808533%source coverage.899unknown
cells blocked. SHA256 e2efb4120fdaddfae4cd4b7cedea8f9f187f63d90fa4cf1535ce140f21d8c050.
Both arms reuse this surface independently of the background dataset.

Background process recorded in `data/traffic-geography-national/worker-process.json`,
SQLite queue and worker.log in same directory.13,035tiles across84provided atlas
boundaries;50Stavropol tiles prioritized. This is not yet complete national coverage.
Local vector cache:1,655,389buildings/42,316water/223protected features from
north-caucasus-261107.osm.pbf;15truncated protected relations repaired using official
OSM full-relation responses, versions/hash/mixed timestamps retained. Exact source
polygon gates local-cache eligibility; other tiles use Overpass. DEM GLO30 real
southern-neighbor sampling fixes half-pixel seams, with no invented elevations.
Queue resumes interrupted work, retries failures, stops at disk safeguards.
Current workerPID72716; survives this turn, not configured for automatic reboot.
Manual resume: `backend/.venv/bin/python -m synthetic_traffic.geography_queue run
--output data/traffic-geography-national --vector-cache
data/traffic-geography-national/vector-cache.sqlite`. Stop via STOP file in output.
Sources/code are implemented locally; application has not been restarted.

First frozen A/B completed: `llm-comparison/result.json` and corrected provenance
`llm-comparison/attribution-summary.json`. Inputs/source hashes stable. Automatic:
128corridors,13.112s generation,73.318s verification,41index-verified/3timeouts,0gain.
With11LLMhypotheses:128corridors including8LLM (7alsoautomatic),13.335s generation,
60.151s verification,16index-verified/5timeouts,0gain. Only1LLM-exposed project
completed index verification, so this does not establish LLM usefulness or uselessness.
Both use4420syntheticOD/67zones/180markets; prep46.078s. Selected window intersects
Stavropol/Karachay-Cherkessia/Krasnodar; reported objective population-weighted across
those3regions. Baseline95.11640098918427. First run interrupted in sharedpreparation
before protocol freeze to fix agent_hypothesis origin recognition; no outcomeslost.
Verification overshoot observed (17.57s and14.25s indexcalls despite5s slices); fixpending.
Checks:483backendunit +Ruff/mypy319passed,50ClickHouseintegrationpassed afterloading
.env.analytics (initialrunfailedbecauseenvironmentmissing);69focusedETLpassed.
Frontend509tests/build/typecheck/lint/36rules passed earlierthisturn. No deployment.

User superseded minute verification:300s exact checking after120s generation.
INDEX_CANDIDATE_SECONDS=60, alwayscappedbyremainingoverall300s; searchdefault/max300.
Progress,evidence,runnerprotocoluseproductionconstants.8search+6backendtimingtests
passed. Per-marketdeadlinechecks now cover index city/regionreads andfinalreturn;
oneblockingIO/NumPyoperation can stilloverrun, so this is cooperative cancellation.
User questioned30km/h highways: previousconnection_design interpreted rastergrid
corner asphysicalcurve andlimitedwholecorridor30. That pilot remainsdiagnostic,
notcredibleengineeredhighwaybenefit evidence. Alignment smoothing/localtimefixpending.
Reference forgridartifactandline-of-sight routing: Nash et al., AAAI2007 Theta*,
https://f.aaai.org/Papers/AAAI/2007/AAAI07-187.pdf ; ourpost-smoothingisnotTheta*.
Curvature/time screening reference: FHWA Speed Concepts chapter4 and Montana
Chapter25 metricpointmassR=V²/[127(e+f)]. Chosenparametersmustremainexplicit
scenarioassumptions, notRussianregulatorycertificationorobservedspeeds:
https://highways.dot.gov/safety/speed-management/speed-concepts-informational-guide/chapter-4-engineering-and-technical
https://www.mdt.mt.gov/other/webdata/external/traffic/manual/chapter_25.pdf

Alignedroadimplementationverified: smoothedfull-cellLOS +screenedcircularfillets,
localcurvature/grade/structuretime, harmonicwhole-routeequivalent speed.
Terrainprofileusesbilinearheightsalongtravelledline; lateralcorner8.62%wasnot
actual2.56%roadgrade. A*nowavoidsdrydiagonalwatercorners,retainsfullbridgefootprint
andbothtunnelanchors. No standalone speedproject.
Actual30sgeneration smoke:12corridors/7949screenedsegments,54.96–58.56km/h,
endpoints,length,summedhoursandappliedgraphhoursmatch.11LLMhypothesesresolved,
8accesseligible but0survivingLLMcorridors;71alignmentrejections. Thisisnot
evidenceofLLMquality. Evidencealignment-smoke.json,alignment-validation.json.
Root40focusedtraffic +4explicitrealcasealignmentregressionspassed;486backend
unit/Ruff/mypy321passed. Frozenrepeat startedinllm-comparison-300s-aligned,
120sgeneration/300sverification/60sperindexcandidate,existingLLMoutputreused.

Readonly3LLMcase diagnostic (llm-alignment-diagnostic-three.json): A*findsroutes
forall3, thenvalidationalongtravelledprofile rejects9.058%/8.625%/8.134%grades
against8%limit; first/thirdareproposedfillets,secondrawsegmentwithoutstructure.
Not generalizedtoall8pairs. 300srepeat automaticgeneration120.202s produced
30validnewcorridors (53.17–59.57km/h),154existingcorridorprojects;228alignment
rejections. Exactindexverification underway.
SouthernvectorpipelineinitiallyfailedinvalidOSMarea3152959140;isolatedrecovery
recordsway1576479570 officialsource+topologyrepair. Producer81177/watcher81178
retry; rootETL untoucheduntil frozenA/Bends. OriginalNorthgeographyworker72716
continues. No incompleteunioncachepublished.

300saligned automatic armfinished:120.191sgeneration,300.184sverification,
8processed/5indexverified/3timeouts,0positivealternatives. All5verifiedscores
exactbaseline95.11640098918427;Stavropol99.15140597565384unchanged. Threezero
checks cost42–46s, two1.1s;timeout60.91/60.08/26.18s. LLMarmnowrunningon
samefrozensources. No claimedindexgain. Readonlyfalse-zeroauditrequested.

FINALaligned300sA/Bcompleted, hashesstabletrue. Auto30corridors/5verified/3timeouts,
300.184sverification; auto+LLM29corridors/6verified/3timeouts,300.197sverification.
Both0confirmedregionalgain;Stavropol99.15140597565384unchangedforverifiedprojects.
LLM11forwarded/8targetseligible/0validcorridors/0indexverifiedLLMhypotheses.
ThisisnotproofLLMuseless; geometricgenerationblockedLLMtest. Timeoutsunknown,
notzerogain. Resultsllm-comparison-300s-aligned/{result,attribution-summary}.json;
publicconciseevidence docs/results/network-hypothesis-pilot.json.
No ongoingsearchafterrun; nationalgeographybackgroundcontinuesseparately.

Archived session detail before compaction:
Implemented: sole adaptive development search, mandatory no-speed CatBoost, geographic corridors/lanes and compiled local diffs. New120s generation + separate300s verification per latest user instruction. Actual LLM returned11hypotheses; firstA/B0verifiedgain, only1LLMproject indexverified. Repeatpending: fixgridcorner30km/hartifact andindexdeadlineovershoot;60s candidate slice within300s implemented/tested; alignmentfix tested on12realcorridors/7949segments. Repeat completed at work/network-development/llm-comparison-300s-aligned: auto5verified/LLMarm6verified, both0gain;3timeouts each. LLM11hypotheses/8eligible/0validcorridors, so LLMindexeffect untested. Sources stable; no active search. Frozen pilot geography99.558%covered;899unknowncells blocked. Background national geography queue running, Stavropolfirst; full region download incomplete. No deployment.

Localruntime started atuserrequest2026-11-12: API127.0.0.1:8007 PID94891,
Vite127.0.0.1:5187 launcherPID94892,currentroot sources. CHAT_ENABLED=true,
GRAPH_DIR=data/graph_ru,TRAFFIC_WORKERS=32;private.env.analyticsloadedwithout
printingcredentials. APIstartup~40s. Directhealth200,proxiedhealth200,regions200;
GET/chat/sessions404waswrongprobe (chatusesPOST/chat),notchatfailure.
Logs/processmanifestwork/local-runtime/. ReplacespriorVite59324; no externaldeployment.
Geographyunionpublished1,510,928,384B,4,978,401buildings/175,680water/439protected;
all50Stavropoltilesvectorcovered. Worker85705switchedand40/50rastertilescomplete;
remaining10failedproviderDNS/DEMwarp,geographyworkerinvestigating. Unionrepair
sourcefilescopiedafterfrozenpilot,9tests/Ruffpass;doesnotaltercompletedpilot.

## Continued local-diff optimization

User asked to continue after local runtime start. Same actualsavedlocallybeneficial
candidate profile before:60.076s timeout; repair180calls48.892s, values8.261s
interrupted. After sparseCSRdelta+marketprefilter+overlay-onlyaggregation:
50.438s fullyverified;158markets/20,411,056overlaynodes;values0.661s,427directly
affectedorigins and2673recomputedbecausemarkettransferschanged. Weightedindex
95.11640098918427→95.11709802871178 (+0.0006970395points), KCHR+0.0136617064;
Stavropol-1.44508e-8 (nomeaningfulgain). Syntheticvehiclehours689.2549→687.6767.
Singleprofile withdifferentcachewarmth/backgroundactivity,notstatisticalspeedupclaim.
Evidenceindex-profile-before/index-profile-after;publicdocs/results/network-index-local-diff.json.
Parallel4-tree repair and boundedalignmentrerouting pending; no new fullLLMpilot yet.
Stavropol50/50rastertilesverified;RFqueuealive96642/session41505,notRFcomplete.
DownloadContent-Lengthguardcopiedand4tests passed.

Bounded4-marketparallelrepair actualsamecandidate30.130s (serial50.438s), exact
regionalvaluesidentical;peakRSS3,376,840,704bytes,158affected/22skippedmarkets.
Per-workerrepairtimesoverlap; wallphase26.918s,fullindex30.130s. Readonlyshared
CSR,privateCOWtrees, atomicpublication; cancellationjoinsallworkersbeforecleanup.
TestsverifyfullDijkstraequality, noremainingthreads/partialpublicationontimeout.
Alignmentlocalizedrerouting now3A*attempts perpairmax, samegrade/obstaclecaps.
Actual30ssmoke9validcorridors/5398segments,2LLMhypotheses survive:
Apsua–Saratovskyattempt3,16.13km/58.02kmh;NovayaDerevnya–Saratovskyattempt2,
10.45km/54.29kmh. Evidencealignment-reroute-smoke.json/validation.json.
499backendunit+Ruff/mypy324 and138ETLtests pass. DownloadContentLengthguard4tests
passed;Stavropol50/50validated. FullsingleLLMproductionpilotstarted
llm-pilot-local-diff,120sgeneration/300sverification,original11savedhypotheses,
no newpaidcall. Sourcesfrozenuntilfinish. Liveper-candidateprogressJSONimplemented.
UI5187/API8007 runningpriorloadedcode; restartAPIafterfinalchecks/run.


## Local-diff LLM pilot, 2026-11-12

Completed `llm-pilot-local-diff`: 19 fully verified, 1 deadline timeout, 2/2 routed LLM hypotheses positive. Generation120.18s + verification300.13s, preparation separate. Single-arm exploratory run, no LLM superiority claim. Evidence: `docs/results/network-llm-pilot-local-diff.json`. Reference index candidate:60.08s timeout before,50.44s serial sparse,30.13s four-worker repair; identical regional values. Checks:499 backend unit,138 ETL tests, Ruff and mypy324 modules passed.

Readonly surrogate audit:9 actual new corridors all predict0.000716841804364. Only length varies in their current vectors; endpoint demand/detour/new travel time absent.759training labels (550train/209heldout),24synthetic9-node networks and2real snapshots; real48labels contain capacity/closure only. Next: grounded connection features, diverse links/packages, schema+artifact retrain, new-road top-k regret and300s yield evaluation. No retraining performed in this iteration.

Stavropol50/50geography tiles verified, Russia queue continues separately; not complete nationwide. Local API restarted to load current source; UI5187 retained.


## Remote branch inspection, 2026-11-12

User requested recentpush onfeat/map-first-ui. Fetched origin:0c7cb89→8d628242647d534316122e51846663a55e3851ff (commitdate2026-11-12 21:59:31MSK,titleasd). Latestcommit changes6documentation/state files only: medicalaccessibilityresearch, territorialindexsurvey, legal-normimplementationplan, runtime/sessionnotes. No frontend/backendsourcechanges in thiscommit. Plan explicitlyresearch-only; proposes medical/MFCpilot thenfirecoverage. No merge/cherry-pick/switch performed; currentdirtyworkpreserved. OlderdivergedUIcommits notassumedmissingfromcurrentimplementationbecausepriorintegrationwasnonancestral.


## Second remote inspection, 2026-11-12

Fetched newpushes: feat/map-first-ui8d62824→bd32de32b70fa41f5b7f13d8e2363bbd833ff974, commit2026-11-12 22:25:54MSK.459files,119608insertions/2046deletions incllargeJSONevidence. Actualnormative domain/usecases/ClickHouse/API, walking/roadpaths andclosures, ninecriteria, sharedmaps/legend/screens. Storedreportnormative-live-index-coverage.json claims754numericregion-servicepairs of756,84territories; mixedconditionalandscenariobases, notlegalcomplianceverification. Codeandreportread, notexecutedhere. No directtraffic_development/search_projects reference innewnormative adapters/usecases; linkingnewsearch effects remainswork.

origin/feat/transport-scenarios-update advanced5daf681→bcc7301 by8commits: chatwrap/alignment/touchtargets,returntoselectedregion,tooltips,seasonallinkswording,newicons/socialcard,READMEvisuals. Currentdirtyrootunchangedexceptsessionnotes; no merge/cherry-pick.
