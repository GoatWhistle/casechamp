import argparse
import hashlib
import json
import os
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from analytics.client import ClickHouse
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.regional_snapshots import RegionalSnapshots
from import_national_inventory import insert_batch
from import_official_employment import facilities_for_region

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'https://portal.22trud.ru/czn'
CLEAN_SHA256 = '8e575b91fa647a9ed83d3950b817cf91fa4efa8456a705e8aa58186449c6afa0'
RAW_SHA256 = 'a924848a78c69cd3db48babe620ae9e995dc5d3b63a1aeff08b0b5bed53bfa92'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw', type=Path, required=True)
    parser.add_argument('--records', type=Path, required=True)
    args = parser.parse_args()
    if hashlib.sha256(args.raw.read_bytes()).hexdigest() != RAW_SHA256:
        raise ValueError('Altai primary source differs from verified official snapshot')
    if hashlib.sha256(args.records.read_bytes()).hexdigest() != CLEAN_SHA256:
        raise ValueError('Altai records differ from verified extraction of primary source')
    records = json.loads(args.records.read_text())
    if not isinstance(records, list) or not records:
        raise ValueError('Altai directory requires published records')
    regions = json.loads((ROOT/'.local/normative-national-inputs/regions.json').read_text())['regions']
    region = next(r for r in regions if r['id']=='01000000')
    metadata = {'id':region['id'],'source_url':SOURCE,'raw_sha256':RAW_SHA256,'retrieved_at':datetime.now(UTC).isoformat()}
    facilities, quality = facilities_for_region(metadata, records, region['bounds'])
    facilities = [replace(f,id=f.id.replace('trudvsem-','portal22-')) for f in facilities]
    if not any(f.latitude is not None for f in facilities):
        raise ValueError('Altai official directory has no accepted employment coordinate')
    reader = ClickHouseReader(os.environ.get('CLICKHOUSE_URL','http://127.0.0.1:18123'),os.environ.get('CLICKHOUSE_USER','plexus'),os.environ['CLICKHOUSE_PASSWORD'],max_threads=1)
    table = 'plexus_normative.service_directories'
    prior = reader.rows(f'SELECT id FROM {table} WHERE region_id={{region:String}} AND source_sha256={{digest:String}} LIMIT 1',{'region':region['id'],'digest':RAW_SHA256})
    if prior:
        print('Verified Altai source already imported',prior[0]['id']);return
    generation = uuid4().hex
    snapshots = RegionalSnapshots(reader,table)
    snapshots.save_facilities(generation,facilities)
    snapshots.load(generation,'facilities',len(facilities))
    header = {'id':generation,'region_id':region['id'],'category':'employment_candidate','observed_at':metadata['retrieved_at'],'source_sha256':RAW_SHA256,'facilities':len(facilities)}
    insert_batch(ClickHouse(),table,[json.dumps(header)])
    proof = {**header,'source_url':SOURCE,'raw_records':len(records),'located':sum(f.latitude is not None for f in facilities),'quality':quality,'coordinate_status':'official_institution_pin','entrances_verified':False}
    (ROOT/'docs/results/normative-altai-employment-import.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(proof,ensure_ascii=False))


if __name__=='__main__':main()
