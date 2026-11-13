from hashlib import file_digest
from pathlib import Path

from synthetic_traffic.origin_store import OriginStore


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return file_digest(stream, 'sha256').hexdigest()


def publish_origins(directory: Path, loads, flows):
    result = {}
    for kind, values in (('loads', loads), ('flows', flows)):
        store = OriginStore(directory / kind, kind)
        hashes = {}
        for origin, value in values.items():
            store[origin] = value
            hashes[str(origin)] = digest(store.directory / f'{origin}.npz')
        result[kind] = hashes
    return result


def read_origins(directory: Path, manifest):
    result = []
    for kind in ('loads', 'flows'):
        for origin, expected in manifest[kind].items():
            if not origin.isdecimal() or str(int(origin)) != origin:
                raise ValueError('Invalid origin identifier')
            if digest(directory / kind / f'{origin}.npz') != expected:
                raise ValueError('Origin snapshot checksum mismatch')
        store = OriginStore(directory / kind, kind, readonly=True)
        if set(store) != {int(origin) for origin in manifest[kind]}:
            raise ValueError('Origin snapshot inventory mismatch')
        result.append(store)
    return result
