import argparse
import gzip
import hashlib
import json
import os
import re
from pathlib import Path

from analytics.client import ClickHouse
from app.domain.normative.model import Facility
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.regional_snapshots import RegionalSnapshots
from import_national_inventory import insert_batch

ROOT = Path(__file__).resolve().parents[1]


def checked_bytes(root, path, expected):
    target = (root/path).resolve()
    if not target.is_relative_to(root.resolve()):raise ValueError('Source path escapes acquisition root')
    content = target.read_bytes()
    if hashlib.sha256(content).hexdigest() != expected:raise ValueError('Official directory source hash differs')
    return content


def facilities_for_region(meta, records, bounds):
    result, seen = [], set()
    quality = {'duplicates':0,'geometry_rejected':0,'profile_rejected':0}
    for record in records:
        identity = hashlib.sha256(json.dumps(record,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:24]
        if identity in seen:
            quality['duplicates']+=1;continue
        seen.add(identity)
        latitude,longitude = record['latitude'],record['longitude']
        profile = bool(re.search(r'занятост|кадров|цзн|работ',record['name'],re.I))
        west,south,east,north = bounds
        located = isinstance(latitude,(int,float)) and isinstance(longitude,(int,float)) and south<=latitude<=north and (west<=longitude<=east if west<=east else longitude>=west or longitude<=east)
        if not located:quality['geometry_rejected']+=1
        if not profile:quality['profile_rejected']+=1
        usable = located and profile
        source = meta['source_url'];digest = meta['raw_sha256']
        result.append(Facility(
            'trudvsem-'+meta['id']+'-'+identity,'employment',record['name'],record['address'],
            source,meta['retrieved_at'],latitude if usable else None,longitude if usable else None,
            source if usable else None,'official_institution_pin' if usable else 'missing',
            source_sha256=digest,coordinate_snapshot_sha256=digest if usable else None,
            coordinate_snapshot_url=source if usable else None,
        ))
    return result,quality


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source-root',type=Path,required=True);args=parser.parse_args()
    source_root=args.source_root.resolve()
    manifest=json.loads((source_root/'.local/research/employment-national/manifest.json').read_text())
    regions={r['id']:r for r in json.loads((ROOT/'.local/normative-national-inputs/regions.json').read_text())['regions']}
    if {m['id'] for m in manifest}!=set(regions) or len(manifest)!=len(regions):raise ValueError('All project regions require one verified directory snapshot')
    reader=ClickHouseReader(os.environ.get('CLICKHOUSE_URL','http://127.0.0.1:18123'),os.environ.get('CLICKHOUSE_USER','plexus'),os.environ['CLICKHOUSE_PASSWORD'],max_threads=1)
    client=ClickHouse();table='plexus_normative.service_directories';snapshots=RegionalSnapshots(reader,table);proof=[]
    for sql in (ROOT/'infra/clickhouse/normative-service-directories.sql').read_text().split(';'):
        if sql.strip():client.request(sql)
    for meta in manifest:
        if meta['status']!='verified_selected' or meta['actual_region_code']!=meta['provider_code'] or meta['source_url']!='https://trudvsem.ru/czn':raise ValueError('Official source selection is unverified')
        raw=checked_bytes(source_root,meta['raw_path'],meta['raw_sha256'])
        html=gzip.decompress(raw) if raw[:2]==b'\x1f\x8b' else raw
        selected=re.search(rb'window.currentRegionCode\s*=\s*"([0-9]+)"',html)
        if not selected or selected.group(1).decode()!=meta['provider_code']:raise ValueError('Raw official page has another region')
        records=json.loads(checked_bytes(source_root,meta['centers_path'],meta['centers_sha256']))
        if len(records)!=meta['center_count']:raise ValueError('Official directory record count differs')
        facilities,quality=facilities_for_region(meta,records,regions[meta['id']]['bounds'])
        generation=hashlib.sha256((meta['id']+meta['raw_sha256']+'employment-profile-bbox-v1').encode()).hexdigest()
        exists=reader.rows(f'SELECT id FROM {table} WHERE id={{id:String}} LIMIT 1',{'id':generation})
        if not exists:
            snapshots.save_facilities(generation,facilities)
            snapshots.load(generation,'facilities',len(facilities))
            header={'id':generation,'region_id':meta['id'],'category':'employment_candidate','observed_at':meta['retrieved_at'],'source_sha256':meta['raw_sha256'],'facilities':len(facilities)}
            insert_batch(client,table,[json.dumps(header)])
        proof.append({'region_id':meta['id'],'generation':generation,'records':len(records),'facilities':len(facilities),'located':sum(f.latitude is not None for f in facilities),'quality':quality,'source':meta})
        print('Official employment imported',meta['id'],len(facilities),flush=True)
    (ROOT/'docs/results/normative-official-employment-import.json').write_text(json.dumps({'regions':len(proof),'facilities':sum(r['facilities'] for r in proof),'located':sum(r['located'] for r in proof),'method':'Official regional map replaces OSM employment targets; exact duplicates removed, out-of-bbox or unclear-name profiles kept with missing geometry; no assumed coordinate repair or entrance verification','results':proof},ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
