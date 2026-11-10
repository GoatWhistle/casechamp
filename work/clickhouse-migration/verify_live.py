import json
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request,urlopen

BASE='http://127.0.0.1:8001/api/v1/'
def get(path):
    with urlopen(BASE+quote(path,safe='?=&/'),timeout=90) as response:return json.load(response)

def post(path,body):
    with urlopen(Request(BASE+path,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'}),timeout=90) as response:return json.load(response)

report={'api':[]}
for path,expected in json.loads(Path('work/clickhouse-migration/api-before.json').read_text()).items():
    start=time.monotonic();actual=get(path)
    equal=actual==expected if path!='airports' else actual['airports']==expected['airports']
    assert equal,path
    report['api'].append({'path':path,'equal':equal,'seconds':time.monotonic()-start})
analyses=get('road-analyses')
assert all(a['compatible'] for a in analyses)
assert next(a for a in analyses if a['id']=='94a058ce9c3a48fa85e251079275e2db')['status']=='paused'
old=next(j for j in get('road-scenarios') if j['addition'] is not None and j['status']=='completed')
body={'region_id':old['region_id'],**{k:old['addition'][k] for k in ('source_node','target_node','travel_hours')},'money':old['money_assumptions']}
new=post('road-connections',body)
while new['status'] in ('queued','running'):
    time.sleep(1)
    new=get('road-scenarios/'+new['id'])
    print('calculation',new['status'],new['completed'],flush=True)
assert new['status']=='completed',new.get('error')
for key in ('before','after','delta','population','settlements','affected_settlements','settlement_effects','money'):
    assert new['result'][key]==old['result'][key],key
report['calculation']={'id':new['id'],'compared_to':old['id'],'status':new['status'],'numerically_equal':True,'seconds':new['result']['elapsed_seconds']}
view=get('road-graph?west=38&south=54&east=43&north=57&zoom=7')
report['road_view']={'segments':len(view['segments']),'matched':view['matched']}
assert len(view['segments'])>0
Path('work/clickhouse-migration/live-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(report['calculation'],report['road_view'],flush=True)
