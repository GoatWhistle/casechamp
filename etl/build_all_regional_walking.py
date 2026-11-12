import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--extract-only', action='store_true')
    args = parser.parse_args()
    manifest = json.loads((ROOT / '.local/normative-national-inputs/osm/manifest.json').read_text())
    for source in sorted(manifest, key=lambda row: row['bytes']):
        subprocess.run([sys.executable, 'etl/extract_regional_walking.py', '--district', source['id']], cwd=ROOT, check=True)
    if args.extract_only:
        return
    regions = json.loads((ROOT / '.local/normative-national-inputs/regions.json').read_text())['regions']
    for region in regions:
        subprocess.run([sys.executable, 'etl/assemble_regional_walking.py', '--region-id', region['id'], '--import-storage'], cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
