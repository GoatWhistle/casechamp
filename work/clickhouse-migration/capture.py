import json
from pathlib import Path
from urllib.request import urlopen

routes=['overview','regions?season=winter','regions?season=summer','geo/regions','geo/boundaries','sources','airports','regions/17000000?season=winter','regions/17000000/links?season=winter&include_unknown=true','regions/17000000/settlements?sort=population&order=desc&limit=25&offset=0','search?q=Владимир']
from urllib.parse import quote
result={}
for path in routes:
 try:
  with urlopen('http://127.0.0.1:8001/api/v1/'+quote(path,safe='?=&/'),timeout=90) as r: result[path]=json.load(r)
 except Exception as error: result[path]={'error':str(error)}
 print(path,flush=True)
Path('work/clickhouse-migration/api-before.json').write_text(json.dumps(result,ensure_ascii=False))
