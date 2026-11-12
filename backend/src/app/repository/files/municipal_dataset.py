import gzip
import json
import os
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from app.domain.errors import DataUnavailable
from app.domain.normative.index import IndexValue
from app.domain.normative.model import AccessRow
from app.domain.normative.scenario_index import scenario_policy
from app.usecase.municipal_dataset import (
    MunicipalSnapshotSource,
    municipal_boundary_digest,
    snapshot_digest,
)
from app.usecase.municipal_service_models import MunicipalNormativeValue
from app.usecase.municipalities import Municipality


def _json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()


def _restore(record: dict[str, Any]) -> MunicipalNormativeValue:
    return MunicipalNormativeValue(
        **{
            **record,
            "thresholds": tuple(record["thresholds"]),
            "values": tuple(IndexValue(**value) for value in record["values"]),
            "source_urls": tuple(record["source_urls"]),
        }
    )


class JsonMunicipalDataset:
    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def _write(self, path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary: str | None = None
        try:
            with NamedTemporaryFile(dir=path.parent, delete=False) as stream:
                temporary = stream.name
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)

    def _source_path(self, digest: str) -> Path:
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise ValueError("Invalid municipal dataset SHA256")
        return self.directory / "sources" / digest

    def boundaries(self, municipalities: list[Municipality]) -> str:
        digest = municipal_boundary_digest(municipalities)
        if not municipalities:
            return digest
        region = municipalities[0].region_id
        if any(item.region_id != region for item in municipalities):
            raise ValueError("Boundary snapshot must contain one region")
        path = self.directory / "boundaries" / digest
        content = gzip.compress(
            _json([asdict(item) for item in sorted(municipalities, key=lambda item: item.id)]),
            mtime=0,
        )
        self._write(path / "boundaries.json.gz", content)
        self._write(
            path / "manifest.json",
            _json(
                {
                    "boundary_snapshot_sha256": digest,
                    "compressed_sha256": sha256(content).hexdigest(),
                    "region_id": region,
                    "municipalities": len(municipalities),
                    "assignment": "original_polygon_covers_unique_owner_shared_boundaries_excluded",
                }
            ),
        )
        self._write(
            self.directory / "boundary-regions" / (sha256(region.encode()).hexdigest() + ".json"),
            _json({"boundary_snapshot_sha256": digest}),
        )
        return digest

    def find_boundaries(self, region_id: str) -> str | None:
        path = (
            self.directory / "boundary-regions" / (sha256(region_id.encode()).hexdigest() + ".json")
        )
        return json.loads(path.read_bytes())["boundary_snapshot_sha256"] if path.exists() else None

    def snapshot(self, source: MunicipalSnapshotSource, rows: list[AccessRow]) -> str:
        digest = snapshot_digest(source, rows)
        path = self._source_path(digest)
        if (path / "manifest.json").exists():
            return digest
        content = b"".join(
            _json(asdict(row)) + b"\n" for row in sorted(rows, key=lambda item: item.id)
        )
        compressed = gzip.compress(content, mtime=0)
        self._write(path / "measurements.jsonl.gz", compressed)
        self._write(
            path / "manifest.json",
            _json(
                {
                    "schema_version": "municipal-dataset-v1",
                    "source_sha256": digest,
                    "source": asdict(source),
                    "points": len(rows),
                    "measurements_sha256": sha256(compressed).hexdigest(),
                }
            ),
        )
        run_key = sha256(
            _json((source.region_id, source.criterion_id, source.run_id, source.stage))
        ).hexdigest()
        self._write(self.directory / "runs" / (run_key + ".json"), _json({"source_sha256": digest}))
        return digest

    def find_run(self, region_id: str, criterion_id: str, run_id: str, stage: str) -> str | None:
        run_key = sha256(_json((region_id, criterion_id, run_id, stage))).hexdigest()
        path = self.directory / "runs" / (run_key + ".json")
        return json.loads(path.read_bytes())["source_sha256"] if path.exists() else None

    def source(self, source_sha256: str) -> MunicipalSnapshotSource:
        try:
            record = json.loads((self._source_path(source_sha256) / "manifest.json").read_bytes())
            return MunicipalSnapshotSource(**record["source"])
        except (OSError, ValueError, TypeError, KeyError) as error:
            raise DataUnavailable("Municipal route snapshot manifest is unavailable") from error

    def rows(self, source_sha256: str) -> list[AccessRow]:
        path = self._source_path(source_sha256)
        try:
            manifest = json.loads((path / "manifest.json").read_bytes())
            compressed = (path / "measurements.jsonl.gz").read_bytes()
            if sha256(compressed).hexdigest() != manifest["measurements_sha256"]:
                raise ValueError("Municipal point snapshot checksum differs")
            rows = []
            for line in gzip.decompress(compressed).splitlines():
                row = json.loads(line)
                rows.append(AccessRow(**{**row, "uncertainty": tuple(row.get("uncertainty", []))}))
            if (
                len(rows) != manifest["points"]
                or snapshot_digest(self.source(source_sha256), rows) != source_sha256
            ):
                raise ValueError("Municipal point snapshot is incomplete")
            return rows
        except (OSError, ValueError, TypeError, KeyError, EOFError) as error:
            raise DataUnavailable("Municipal route snapshot is unavailable") from error

    def _key(self, municipality: Municipality, criterion_id: str, version: str) -> str:
        return sha256(
            _json(
                (
                    municipality.region_id,
                    municipality.id,
                    municipality.source_sha256,
                    municipality.coordinates,
                    "municipal-aggregate-v3",
                    criterion_id,
                    scenario_policy(criterion_id).definition_sha256,
                    version,
                )
            )
        ).hexdigest()

    def aggregate(
        self,
        source_sha256: str,
        municipality: Municipality,
        value: MunicipalNormativeValue,
        point_ids: list[str],
        source_key: str | None = None,
        boundary_snapshot_sha256: str | None = None,
    ) -> None:
        boundary_sha = (
            boundary_snapshot_sha256 or self.find_boundaries(municipality.region_id) or ""
        )
        identifier = self._key(municipality, value.criterion_id, source_sha256 + boundary_sha)
        payload = {
            "aggregation_method": "municipal-aggregate-v3",
            "boundary_snapshot_sha256": boundary_sha,
            "source_sha256": source_sha256,
            "region_id": municipality.region_id,
            "municipality_id": municipality.id,
            "boundary_source_sha256": municipality.source_sha256,
            "boundary_geometry_sha256": sha256(_json(municipality.coordinates)).hexdigest(),
            "policy_sha256": scenario_policy(value.criterion_id).definition_sha256,
            "point_ids": point_ids,
            "value": asdict(value),
        }
        self._write(self.directory / "aggregates" / (identifier + ".json"), _json(payload))
        if source_key:
            self._write(
                self.directory
                / "runtime"
                / (self._key(municipality, value.criterion_id, source_key) + ".json"),
                _json({"aggregate": identifier}),
            )

    def existing(
        self,
        source_sha256: str,
        municipality: Municipality,
        criterion_id: str,
        boundary_snapshot_sha256: str | None = None,
    ) -> MunicipalNormativeValue | None:
        boundary_sha = (
            boundary_snapshot_sha256 or self.find_boundaries(municipality.region_id) or ""
        )
        path = (
            self.directory
            / "aggregates"
            / (self._key(municipality, criterion_id, source_sha256 + boundary_sha) + ".json")
        )
        if not path.exists():
            return None
        return _restore(json.loads(path.read_bytes())["value"])

    def lookup(
        self, municipality: Municipality, criterion_id: str, source_key: str
    ) -> MunicipalNormativeValue | None:
        path = (
            self.directory
            / "runtime"
            / (self._key(municipality, criterion_id, source_key) + ".json")
        )
        if not path.exists():
            return None
        pointer = json.loads(path.read_bytes())["aggregate"]
        if len(pointer) != 64 or any(character not in "0123456789abcdef" for character in pointer):
            raise DataUnavailable("Municipal aggregate identifier is invalid")
        record = json.loads((self.directory / "aggregates" / (pointer + ".json")).read_bytes())
        return _restore(record["value"])
