import json
from pathlib import Path
from synthetic_traffic.model import Trip
from synthetic_traffic.report import compare
from synthetic_traffic.source import load_network

base=Path('data/additional/synthetic-traffic')
network=load_network(base/'nevinnomyssk-snapshot-v3')
trips=[Trip(**row) for row in json.loads((base/'nevinnomyssk-connection-v1/demand.json').read_text())]
projects=[{'name':'add_lane_at_bottleneck','kind':'capacity','way_ids':[235963363],'extra_lanes':1}]
result=compare(network,trips,projects,Path('presentation/municipal-demo/improvement-stavropol'),1,600,.0001,{'scope':'same saved synthetic OD demand; stress multiplier 1.3; not observed congestion','snapshot':'nevinnomyssk-snapshot-v3'},[1.3])
print(json.dumps(result['cases'],ensure_ascii=False))
