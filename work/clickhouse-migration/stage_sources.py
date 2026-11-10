import argparse
import hashlib
import json
from pathlib import Path

from client import ClickHouse

ROOT=Path.cwd()
MANIFEST=ROOT/'work/clickhouse-migration/removed-sources.json'
HOLD=ROOT/'work/clickhouse-migration/source-hold'


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['check','stage','delete','restore']);args=parser.parse_args()
    if args.action in ('delete','restore'):
        rows=json.loads(MANIFEST.read_text())['files']
        for row in rows:
            staged=HOLD/row['path']
            if not staged.exists():raise RuntimeError('Missing staged file: '+row['path'])
            if digest(staged)!=row['sha256']:raise RuntimeError('Changed staged file: '+row['path'])
        for row in rows:
            staged=HOLD/row['path']
            if args.action=='delete':staged.unlink()
            else:
                original=ROOT/row['path'];original.parent.mkdir(parents=True,exist_ok=True)
                if original.exists():raise RuntimeError('Restoration would overwrite '+row['path'])
                staged.rename(original)
        manifest=json.loads(MANIFEST.read_text());manifest['status']='deleted' if args.action=='delete' else 'restored';MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
        print(args.action,len(rows));return
    c=ClickHouse();old=json.loads((ROOT/'data/analytics-import.json').read_text());rows=[]
    for path,key in [('data/casechamp.duckdb','plexus_casechamp.idx_np'),('data/additional.duckdb','plexus_additional.settlements')]:
        group=key.split('.')[0]
        checksum=next(v for k,v in old['fingerprints'].items() if k.startswith(group+'.'))
        file=ROOT/path
        assert digest(file)==checksum,path
        rows.append({'path':path,'sha256':checksum,'bytes':file.stat().st_size})
    for file in sorted((ROOT/'data/graph_ru').glob('*.parquet')):
        checksum=old['fingerprints']['plexus_graph.'+file.stem]
        assert digest(file)==checksum,str(file)
        rows.append({'path':str(file.relative_to(ROOT)),'sha256':checksum,'bytes':file.stat().st_size})
    for table in old['tables']:
        assert int(c.rows('SELECT count() AS n FROM '+table['table'])[0]['n'])==table['rows']
    for record in c.rows('SELECT path,sha256,lower(hex(SHA256(body))) AS actual FROM plexus_atlas.documents'):
        file=ROOT/'frontend/atlas/public'/record['path']
        assert digest(file)==record['sha256']==record['actual'],str(file)
        rows.append({'path':str(file.relative_to(ROOT)),'sha256':record['sha256'],'bytes':file.stat().st_size})
    for path in json.loads((ROOT/'work/clickhouse-migration/state.json').read_text())['files']:
        file=ROOT/path;rows.append({'path':path,'sha256':digest(file),'bytes':file.stat().st_size})
    total=sum(r['bytes'] for r in rows)
    print('verified files',len(rows),'bytes',total,flush=True)
    if args.action=='check':return
    if HOLD.exists() and any(HOLD.rglob('*')):raise RuntimeError('Staging folder is not empty')
    c.request('CREATE TABLE IF NOT EXISTS plexus_atlas.migrated_sources (path String,sha256 String,bytes UInt64) ENGINE=MergeTree ORDER BY path')
    for row in rows:
        c.request('INSERT INTO plexus_atlas.migrated_sources FORMAT JSONEachRow',json.dumps(row).encode())
    MANIFEST.write_text(json.dumps({'status':'staged','bytes':total,'files':rows},ensure_ascii=False,indent=2))
    for row in rows:
        path=ROOT/row['path'];target=HOLD/row['path'];target.parent.mkdir(parents=True,exist_ok=True);path.rename(target)
    print('staged',len(rows),flush=True)

if __name__=='__main__':main()
