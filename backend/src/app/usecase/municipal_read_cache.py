import json
from collections.abc import Callable
from hashlib import sha256
from threading import Lock
from typing import Protocol


class MunicipalCacheStore(Protocol):
    def get(self, key: str) -> str | None: ...
    def put(self, key: str, value: str) -> None: ...


class MunicipalReadCache:
    def __init__(self, store: MunicipalCacheStore, revision: Callable[[], str]) -> None:
        self.store, self.revision = store, revision
        self.lock = Lock()

    def read(self, action: str, parameters: dict[str, object], calculate: Callable[[], str]) -> str:
        with self.lock:
            revision = self.revision()
            key = sha256(json.dumps({'format': 'municipal_agent_reads_v1', 'revision': revision,
                                    'action': action, 'parameters': parameters}, sort_keys=True).encode()).hexdigest()
            cached = self.store.get(key)
            if cached is not None:
                return cached
            result = calculate()
            if self.revision() == revision:
                self.store.put(key, result)
            return result
