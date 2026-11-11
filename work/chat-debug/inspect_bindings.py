import os

from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot
from app.settings import load_settings

settings = load_settings(os.environ)
reader = ClickHouseReader(settings.clickhouse_url, settings.clickhouse_user, settings.clickhouse_password)
snapshot = ClickHouseGraphSnapshot(reader)
missing = []
for query in ("Москва, Москва", "Санкт-Петербург, Санкт-Петербург"):
    places = snapshot.read("corridor_places", {"query": query})
    for place in places:
        attachments = snapshot.read("route_points", {"points": [str(place[0])]})
        market = reader.rows("SELECT city,oktmo,node,snap_h FROM plexus_casechamp.market_cities WHERE oktmo={id:String}", {"id": str(place[0])})
        print({"place": place, "route_points": attachments, "market": market})
        if not attachments or attachments[0][1] is None or int(attachments[0][1]) < 0:
            missing.append(query)
assert not missing, f"Resolved cities missing road attachments: {missing}"
