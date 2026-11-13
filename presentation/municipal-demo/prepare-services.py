import gzip
import json
from pathlib import Path

root=Path('presentation/municipal-demo')
configs=[('N01','Медицина','До 60 минут на машине','minutes',60),('N04','Школы','До 500 метров пешком','distance_metres',500),('N09','Остановки','До 500 метров пешком','distance_metres',500)]
with gzip.open('datasets/municipal-indices/municipal-indices.jsonl.gz','rt') as stream:
    rows=[json.loads(line) for line in stream]
services=[]
for criterion,title,threshold_label,field,threshold in configs:
    record=next(row for row in rows if row['municipality_id']=='osm-relation-1030121' and row['value']['criterion_id']==criterion)
    selected=set(record['point_ids'])
    folder=Path('datasets/municipal-indices/sources')/record['source_sha256']
    with gzip.open(folder/'measurements.jsonl.gz','rt') as stream:
        points=[json.loads(line) for line in stream]
    points=[p for p in points if p['id'] in selected]
    summary=record['value']['values'][0]
    within=sum(p[field] is not None and p[field]<=threshold for p in points)
    assert within==summary['within_points'] and len(points)==summary['reference_points']
    services.append({'id':criterion,'title':title,'thresholdLabel':threshold_label,'threshold':threshold,'value':summary['point_share_percent'],'within':within,'total':len(points),'outside':len(points)-within,'sha256':record['source_sha256'],'points':[{'name':p['name'],'xy':[p['longitude'],p['latitude']],'within':p[field] is not None and p[field]<=threshold,'travel':p[field]} for p in points]})
municipality=next(f for f in json.loads(Path('datasets/municipal-boundaries/municipalities.geojson').read_text())['features'] if f['properties']['id']=='osm-relation-1030121')
(root/'services.json').write_text(json.dumps({'municipality':municipality,'services':services},ensure_ascii=False))
print([(s['title'],s['value'],s['within'],s['total']) for s in services])
