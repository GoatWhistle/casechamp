## Current state

Completed road capacity integration and local activation, 2026-11-11.
Branch feat/map-first-ui, HEAD cdb2c2e1108bde7ff37ab91f9d7907d05de2a897. No new commit,
push or remote deployment. Preserve all unrelated uncommitted appraisal/chat/map work,
root HTML, pyproject.toml/uv.lock. Previous details: [archive](../work/road-capacity/session-before-capacity.md),
[source sync](../work/latest-sync/README.md). Current full runbook: [capacity](../work/road-capacity/README.md).

IMPLEMENTED+LOCALLY VERIFIED: shared road-capacity-v1 domain function for ETL/runtime;
typed lane/direction/speed profiles; UI/API/agent profile changes; passenger appraisal
and routedfreight withtime+km fromsamefastestroadpath. Manual freight preserved.
Missinglanes1perdirection/oneway1total, unknownflowfreeflow. Confirmedhourlyflowonly
addsdelay. Uniform1800PCU/h/lane+BPR.15/4 uncalibrated. Currentflowprofilesconfirmed0.
No invented link demand or highway indexbonus. RAI/rawpopulation/GRP/firms unchanged.

All155747points×3seasons recomputed (467241rows),84sourceregions retained,82publicregions/
246records published. Active4,301,210-way topology unchanged. Legacyundirected72h routing
withtrunkallscenarios retained; separatelargerrefreshgraph NOTactivated. Source trafficrun
roadtraffic20261111v1. Artifactadeb4170a71a6b9bbb8b5b5fe6de0a627e1e9a83b483e0328a0b172cb2964b29.
62,182ways cappedbylegalmaxspeed; publicroadmeanHansen99.12730233->98.45364148 onfixedscale.
[Method/limits](../docs/road-capacity.md), [28nationalchecks](../docs/results/road-capacity-validation.json),
[regionalchanges](../docs/results/road-capacity-regional-comparison.csv).
96independentpointformulas and252runtimebaselines agree; maxHansenerror3.6e-12.

14tables exchangedmetadatalast; oldtables inplexus_capacity_* keptforrollback.
Journaldata/road-capacity/activation.json containsallUUIDs. Samecheckpoint/output only;
freeze rejectsoccupiednamespacewithoutmarker. API mustbestoppedforactivation/rollback.
Schema migration preserved14legacyjobs/checksum4085951559150447410. Backup
plexus_state.road_jobs_before_capacity_v1. TwoalreadycancelledAPIjobs reconciledfromstale
DBqueuedstate beforemigration. Repeatmigrationalready_current andactivationcompletedverified.
StartupcacheJSONkeybug fixed+regressiontest. See workrunbook forclosedtemporarycheckfailures.

LOCALRUNNING: API8007 PID50320 GRAPH_DIR=data CHAT_ENABLED=true ROAD_WORKERS=6;
Vite5187 PID8599 proxies8007. Bothhealthok, queueidle,17jobsincludingall14legacyjobsreadable.
Graphiti owns8001, untouched. MainClickHouse18123 via.env.analytics. No paidmodelcalls.

ChecksPASS: backendRuff/mypy208files/300unit/45integration; frontend36rules/typecheck/
Biome/448unit/build;28capacityunit+1realaggregate+1realmigrationfixture;3desktopE2E42s
withkeyboard,axe,persistence/reload.1440visuallyinspected,1920screenshot; nomobilechecks.
[Finalchecks](../docs/results/road-capacity-checks.json). gitdiffcheck/contextbudgetPASS.

[Liveverification](../docs/results/road-capacity-live-validation.json): VolzhskytoVolgograd,
fiveexistingways. Lanesonlyjob664cbd1d3e5748c8898d816174585ab7 gaveHansen/grossbenefit0;
profilejobc286723f4acc4dfa8218ed95e882d0d6 cut26.94->24.29min,Hansen+0.0840561.
Trips/rates/costssyntheticexplicitassumptions, notobservedtrafficorconstructionproposal.
Freightvehicleconstraints remainunverified. No required implementation work remains.

