import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'etl/analytics'), str(ROOT / 'backend/src')]
import build_roads
import index_corridors
import index_runtime
from client import ClickHouse

DEST = ROOT / 'data/road-refresh'


class StagingClient(ClickHouse):
    def request(self, sql, body=None, size=0):
        if sql.startswith('ALTER TABLE plexus_atlas.atlas_settlements'):
            return b''
        for source in ['graph', 'casechamp']:
            sql = sql.replace('plexus_' + source, 'plexus_refresh_' + source)
        return super().request(sql, body, size)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--wait', action='store_true')
    args = parser.parse_args()
    state_path = DEST / 'staged-derived.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    for part, modules in [('graph', [('roads', build_roads)]), ('calculation', [('runtime', index_runtime), ('corridors', index_corridors)])]:
        ready = DEST / f'staged-{part}.json'
        while not ready.exists() or not json.loads(ready.read_text()).get('complete'):
            if not args.wait:
                raise SystemExit(f'Missing completed {ready}')
            time.sleep(30)
        for name, module in modules:
            if state.get(name):
                continue
            module.ClickHouse = StagingClient
            if name == 'roads':
                root = DEST / 'derived-build'
                (root / 'data').mkdir(parents=True, exist_ok=True)
                graph = root / 'data/graph_ru'
                if not graph.exists():
                    graph.symlink_to(DEST / 'graph', target_is_directory=True)
                sys.argv = ['build_roads', '--root', str(root)]
            module.main()
            state[name] = True
            state_path.write_text(json.dumps(state, indent=2))
    print('All derived staging tables ready', flush=True)


if __name__ == '__main__':
    main()
