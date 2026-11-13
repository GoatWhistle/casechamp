import json
import shutil
from hashlib import sha256
from pathlib import Path

root = Path(__file__).resolve().parents[2]
source = Path(__file__).resolve().parent
snapshot = root / "data/additional/synthetic-traffic/national-snapshot-v2"
if not (snapshot / "source.json").is_file():
    raise SystemExit("Restore the national graph archive into data/ first")
for original in (source / "municipal-traffic-baselines").iterdir():
    target = root / "data/municipal-traffic-baselines" / original.name
    if target.exists():
        continue
    shutil.copytree(original, target)
    record = json.loads((target / "state.json").read_text())
    record["snapshot"] = str(snapshot)
    payload = json.dumps(record, allow_nan=False, separators=(",", ":"))
    (target / "state.json").write_text(payload)
    (target / "sha256").write_text(sha256(payload.encode()).hexdigest())
cache = root / "data/municipal-agent-cache"
cache.mkdir(parents=True, exist_ok=True)
for original in (source / "municipal-agent-cache").glob("*.json"):
    if not (cache / original.name).exists():
        shutil.copyfile(original, cache / original.name)
print("Published previews restored; source revisions control read-cache reuse")
