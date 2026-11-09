import json
import osmium

class Places(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.matches = []
    def node(self, node):
        place = node.tags.get('place')
        if not place or not node.location.valid():
            return
        lat, lon = node.location.lat, node.location.lon
        if 52.70 <= lat <= 53.02 and 36.45 <= lon <= 37.15:
            self.matches.append({'id':node.id,'lat':lat,'lon':lon,'name':node.tags.get('name'),
                                 'place':place,'oktmo':node.tags.get('ref:OKTMO')})
handler=Places()
handler.apply_file('data/raw/osm_russia/central.osm.pbf', locations=False)
print(json.dumps({'scope':'OSM place-tagged nodes in specified box only; ways and relations excluded',
                  'places':handler.matches},ensure_ascii=False,indent=2))
