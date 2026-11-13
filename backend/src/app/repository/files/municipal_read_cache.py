import json
import os
import re
from pathlib import Path
from tempfile import NamedTemporaryFile


class FileMunicipalReadCache:
    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def _path(self, key: str) -> Path:
        if not re.fullmatch('[a-f0-9]{64}', key):
            raise ValueError('Invalid municipal cache key')
        return self.directory / (key + '.json')

    def get(self, key: str) -> str | None:
        try:
            value = self._path(key).read_text()
            record = json.loads(value)
            return value if isinstance(record, dict) else None
        except (OSError, ValueError):
            return None

    def put(self, key: str, value: str) -> None:
        if not isinstance(json.loads(value), dict):
            raise TypeError('Municipal cache requires a JSON object')
        path = self._path(key)
        self.directory.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(mode='w', dir=self.directory, delete=False) as temporary:
            temporary.write(value)
            temporary.flush()
            os.fsync(temporary.fileno())
            name = temporary.name
        try:
            os.replace(name, path)
        finally:
            Path(name).unlink(missing_ok=True)
