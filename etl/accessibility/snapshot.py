from analytics.client import ClickHouse

TABLES = {
    "plexus_atlas": ("atlas_metadata", "atlas_indices"),
    "plexus_graph": ("region_codes", "points", "edges", "ways"),
    "plexus_casechamp": (
        "idx_np",
        "market_cities",
        "manual_links_ru",
        "stg_intercity",
        "np_city_times",
    ),
}


class SnapshotClient(ClickHouse):
    def __init__(self, database):
        super().__init__()
        self.database = database

    def request(self, sql, body=None, size=0):
        for database, tables in TABLES.items():
            for table in tables:
                sql = sql.replace(database + "." + table, self.database + "." + table)
        return super().request(sql, body, size)


def pin_source(client, revision):
    database = "plexus_access_source_" + revision[:16]
    client.request("CREATE DATABASE IF NOT EXISTS " + database)
    for source, tables in TABLES.items():
        for table in tables:
            target = database + "." + table
            original = source + "." + table
            client.request("CREATE TABLE IF NOT EXISTS " + target + " AS " + original)
            client.request("SYSTEM STOP MERGES " + target)
            count = int(client.rows("SELECT count() AS n FROM " + target)[0]["n"])
            expected = int(client.rows("SELECT count() AS n FROM " + original)[0]["n"])
            if count == 0 and expected:
                client.request(
                    "ALTER TABLE " + target + " ATTACH PARTITION ALL FROM " + original
                )
                count = int(client.rows("SELECT count() AS n FROM " + target)[0]["n"])
            if count != expected:
                raise ValueError("Pinned table count differs from active input")
    return SnapshotClient(database)
