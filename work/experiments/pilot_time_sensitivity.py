import json
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, 'backend/src')
from app.domain.pilot_routing import route
from app.repository.files.pilots import pilot_record

path = Path('frontend/atlas/public/pilots/tuva.json')
pilot = pilot_record(json.loads(path.read_text()))
pair = next(pair for pair in pilot.pairs if pair.id == 'kungurtug-kyzyl')
results = []
for factor in (0.75, 1.0, 1.25, 1.5, 2.0):
    for wait in (True, False):
        for frequency in (2, 4, 7):
            edges = tuple(replace(edge, travel_h=edge.travel_h * factor) if edge.mode == 'road' else replace(edge, frequency_per_week=frequency) if edge.id == 'manual:0' else edge for edge in pilot.edges)
            result = route(edges, pair, 'summer', include_wait=wait)
            results.append({'road_time_multiplier': factor, 'waiting_model': 'uniform_random' if wait else 'none_optimistic', 'frequency_per_week': frequency, 'status': result.status, 'hours': result.total_h, 'route': list(result.edge_ids), 'warnings': list(result.warnings)})
assert len(results) == 30
print(json.dumps({'artifact_version':pilot.artifact_version,'season':'summer','pair':pair.id,'cases':results},ensure_ascii=False,indent=2))
