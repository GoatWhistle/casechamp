import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'etl'))
sys.path.insert(0, str(ROOT / 'tests'))
from test_road_collection import RoadCollectionTests
import test_road_collection

with tempfile.TemporaryDirectory() as directory:
    previous = Path(directory) / 'osm_extract.py'
    previous.write_text(subprocess.check_output(['git', 'show', 'HEAD:etl/osm_extract.py'], text=True))
    spec = importlib.util.spec_from_file_location('previous_extractor', previous)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    test_road_collection.osm_extract = module
    case = RoadCollectionTests('test_public_service_connector_is_preserved_with_real_osm_nodes')
    result = case.defaultTestResult()
    case.run(result)
    if len(result.failures) != 1 or result.errors:
        raise RuntimeError(f'Expected omitted service connector failure: {result.errors}')
    print(result.failures[0][1])
    print('CONFIRMED: original extractor omits the real shared-node connector')
