import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'etl'))
from artifacts import file_record, write_json

OUT = ROOT / 'data/road-refresh/reverse'
OUT.mkdir(parents=True, exist_ok=True)
ids = json.loads((ROOT / 'work/road-coverage/reverse-way-ids.json').read_text())
requests = []


def fetch(kind: str, identifiers: list[int], name: str) -> ET.Element:
    url = f'https://api.openstreetmap.org/api/0.6/{kind}?{kind}=' + ','.join(map(str, identifiers))
    path = OUT / name
    if not path.exists():
        subprocess.run(['curl', '-fsSL', '--retry', '2', '--connect-timeout', '20',
                        '--max-time', '120', '-o', str(path.with_suffix('.part')), url], check=True)
        path.with_suffix('.part').replace(path)
    root = ET.parse(path).getroot()
    requests.append({'url': url, 'file': file_record(path)})
    return root


ways = fetch('ways', ids, 'ways.osm')
nodes = sorted({int(node.attrib['ref']) for way in ways.findall('way') for node in way.findall('nd')})
combined = ET.Element('osm', {'version': '0.6', 'generator': 'road-data-recovery'})
for start in range(0, len(nodes), 400):
    response = fetch('nodes', nodes[start:start + 400], f'nodes-{start}.osm')
    combined.extend(response.findall('node'))
combined.extend(ways.findall('way'))
destination = OUT / 'reverse.osm'
ET.ElementTree(combined).write(destination, encoding='utf-8', xml_declaration=True)
write_json(OUT / 'manifest.json', {
    'retrieved_at': datetime.now(timezone.utc).isoformat(), 'license': 'ODbL-1.0',
    'requested_ways': len(ids), 'returned_ways': len(ways.findall('way')),
    'nodes': len(nodes), 'requests': requests, 'combined': file_record(destination),
})
print(f'Fetched {len(ids)} ways and {len(nodes)} nodes', flush=True)
