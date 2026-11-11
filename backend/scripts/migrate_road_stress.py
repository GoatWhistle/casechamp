import os
from pathlib import Path
from urllib.request import Request, urlopen

from app.settings import load_settings

config = load_settings(os.environ)
source = Path(__file__).resolve().parents[2] / "infra/clickhouse/stress.sql"
for sql in source.read_text().split(";"):
    if sql.strip():
        request = Request(config.clickhouse_url or "http://127.0.0.1:18123", data=sql.encode(),
                          headers={"X-ClickHouse-User": config.clickhouse_user,
                                   "X-ClickHouse-Key": config.clickhouse_password})
        with urlopen(request, timeout=30) as response:
            response.read()
print("Road stress schema ready")
