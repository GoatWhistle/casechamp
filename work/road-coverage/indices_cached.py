import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'data/road-refresh'
sys.path.insert(0, str(ROOT / 'etl'))
import indices
from artifacts import file_record


def cached_rai(points):
    manifest = json.loads((DEST / 'rai-manifest.json').read_text())
    assert manifest['output'] == file_record(DEST / 'rai.parquet')
    assert manifest['implementation'] == file_record(ROOT / 'etl/indices.py')
    assert manifest['graph_manifest_sha256'] == hashlib.sha256((DEST / 'graph/manifest.json').read_bytes()).hexdigest()
    cached = pq.read_table(DEST / 'rai.parquet').to_pandas().set_index('point_id', verify_integrity=True)
    assert set(points.point_id) == set(cached.index)
    ordered = cached.loc[points.point_id]
    np.testing.assert_array_equal(ordered[['lat', 'lon']].to_numpy(), points[['lat', 'lon']].to_numpy())
    distances = ordered.km_allseason_road.to_numpy()
    assert not np.isnan(distances).any() and (distances >= 0).all()
    return distances


if __name__ == '__main__':
    indices.rai = cached_rai
    indices.main()
