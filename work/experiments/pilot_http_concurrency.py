import concurrent.futures
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

base='http://127.0.0.1:18080/api/v1/pilots/tuva'
artifact=Path('frontend/atlas/public/pilots/tuva.json')
original=hashlib.sha256(artifact.read_bytes()).hexdigest()
def get():
    with urllib.request.urlopen(base,timeout=15) as response:
        return json.load(response)
pilot=get()
def post(payload):
    request=urllib.request.Request(base+'/evaluate',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
    start=time.perf_counter()
    try:
        with urllib.request.urlopen(request,timeout=15) as response:
            result=(response.status,json.load(response))
    except urllib.error.HTTPError as exc:
        result=(exc.code,json.load(exc))
    return result,time.perf_counter()-start
cases={}
for season in ('summer','winter'):
    for frequency in (2,4,7):
        payload={'season':season,'model_version':pilot['model_version'],'artifact_version':pilot['artifact_version'],'changes':[{'edge_id':'manual:0','frequency_per_week':frequency}]}
        cases[f'{season}-{frequency}']=payload
cases['closed']={'season':'winter','model_version':pilot['model_version'],'artifact_version':pilot['artifact_version'],'changes':[{'edge_id':'manual:5','enabled':False}]}
cases['stale']={**cases['summer-7'],'artifact_version':'stale'}
reference={k:post(v)[0] for k,v in cases.items()}
assert all(reference[k][0]==200 for k in cases if k!='stale')
assert reference['stale'][0]==409
jobs=[key for _ in range(15) for key in cases]
start=time.perf_counter()
with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
    futures=[(key,pool.submit(post,cases[key])) for key in jobs]
    results=[(key,*future.result()) for key,future in futures]
for key,response,duration in results:
    assert response==reference[key],f'mismatch for {key}'
assert get()==pilot
assert hashlib.sha256(artifact.read_bytes()).hexdigest()==original
latencies=sorted(duration for _,_,duration in results)
print(json.dumps({'jobs':len(jobs),'workers':16,'cases':len(cases),'all_equal_to_sequential':True,'stale_status':reference['stale'][0],'artifact_sha256':original,'artifact_unchanged':True,'pilot_response_unchanged':True,'elapsed_s':round(time.perf_counter()-start,3),'p95_s':round(latencies[int(len(latencies)*.95)-1],4),'scope':'single local uvicorn process, loopback, no proxy or external network'},indent=2))
