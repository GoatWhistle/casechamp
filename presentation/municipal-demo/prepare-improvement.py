import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
from scipy.sparse.csgraph import dijkstra
from shapely.geometry import Point, shape
from synthetic_traffic.source import load_network, load_places
from synthetic_traffic.assignment import route_graph

root = Path('presentation/municipal-demo')
source = Path('data/additional/synthetic-traffic/nevinnomyssk-snapshot-v3')
network = load_network(source)
zones, coverage = load_places(source, network)
features = json.loads(Path('datasets/municipal-boundaries/municipalities.geojson').read_text())['features']
municipality = next(f for f in features if 'Кочубеевский' in f['properties']['name'])
polygon = shape(municipality['geometry'])
origins = [z for z in zones if polygon.covers(Point(z.lon,z.lat))]
populations = np.array([z.population for z in zones])
weights = np.array([z.population for z in origins])
values = []
flows = []
for filename in ['baseline-flows-1.3.parquet','flows-1.3-0.parquet']:
    table = pq.read_table(root/'improvement-stavropol'/filename)
    assert np.array_equal(table['way_id'].to_numpy(), network.way_id)
    assert np.array_equal(table['source_node'].to_numpy(), network.raw_nodes[network.source])
    assert np.array_equal(table['target_node'].to_numpy(), network.raw_nodes[network.target])
    hours = table['hours' if 'hours' in table.column_names else 'hours_after'].to_numpy()
    graph, chosen = route_graph(network,hours)
    times = dijkstra(graph,directed=True,indices=[z.node for z in origins])[:,[z.node for z in zones]]
    accessibility = (2 ** (-times/2)) @ populations
    values.append(float(np.average(accessibility,weights=weights)))
    selected = network.way_id == 235963363
    flows.append({'ratio':float(table['demand_capacity_ratio'].to_numpy()[selected].max()),'minutes':float(hours[selected].sum()*60/2)})
selected = np.flatnonzero(network.way_id == 235963363)
roads = [{'type':'Feature','properties':{},'geometry':{'type':'LineString','coordinates':[[float(network.lon[network.source[i]]),float(network.lat[network.source[i]])],[float(network.lon[network.target[i]]),float(network.lat[network.target[i]])]]}} for i in selected]
result = {'municipality':municipality,'road':{'type':'FeatureCollection','features':roads},'before':100,'after':100*values[1]/values[0],'flows':flows,'origins':len(origins),'markets':len(zones),'population':int(weights.sum()),'method':'Population-weighted market accessibility, half-life 2 hours; fixed baseline = 100; markets limited to saved model window; synthetic demand x1.3; identical demand and population before/after','scope':'Scenario index, not the published national-normalized municipal index','change':'One additional lane per direction along OSM way 235963363; construction feasibility not assessed','points':[{'name':z.id,'xy':[z.lon,z.lat]} for z in origins]}
(root/'improvement.json').write_text(json.dumps(result,ensure_ascii=False))
print({k:v for k,v in result.items() if k not in ['municipality','road','points']})
