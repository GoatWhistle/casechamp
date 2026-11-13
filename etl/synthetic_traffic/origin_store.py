from collections.abc import MutableMapping
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np


class OriginStore(MutableMapping):
    def __init__(self, directory: Path, kind: str, base=None, readonly=False):
        self.directory, self.kind = directory, kind
        directory.mkdir(parents=True, exist_ok=True)
        self.base = base if base is not None else {}
        self.origins = set(self.base) | {int(p.stem) for p in directory.glob('*.npz')}
        self.readonly = readonly
        self.temporary = None

    def __len__(self):
        return len(self.origins)

    def __iter__(self):
        return iter(sorted(self.origins))

    def __contains__(self, origin):
        return origin in self.origins

    def __getitem__(self, origin):
        if origin not in self.origins:
            raise KeyError(origin)
        path = self.directory / f'{origin}.npz'
        if not path.exists():
            return self.base[origin]
        with np.load(path, allow_pickle=False) as a:
            if self.kind == 'flows':
                return dict(zip(map(int, a['edges']), map(float, a['amounts']), strict=True))
            return ({(int(u), int(v)): float(w) for u, v, w in
                     zip(a['source'], a['target'], a['amounts'], strict=True)},
                    float(a['missing']),
                    dict(zip(map(int, a['trips']), map(float, a['times']), strict=True)))

    def __setitem__(self, origin, value):
        if self.readonly:
            raise TypeError('Published origin data is immutable')
        if self.kind == 'flows':
            arrays = {'edges': np.fromiter(value, dtype=np.int64),
                      'amounts': np.fromiter(value.values(), dtype=float)}
        else:
            amounts, missing, times = value
            arrays = {'source': np.fromiter((pair[0] for pair in amounts), dtype=np.int64),
                      'target': np.fromiter((pair[1] for pair in amounts), dtype=np.int64),
                      'amounts': np.fromiter(amounts.values(), dtype=float),
                      'missing': np.asarray(missing),
                      'trips': np.fromiter(times, dtype=np.int64),
                      'times': np.fromiter(times.values(), dtype=float)}
        path = self.directory / f'{origin}.npz'
        staging = path.with_suffix('.tmp')
        with staging.open('wb') as stream:
            np.savez_compressed(stream, **arrays)
        staging.replace(path)
        self.origins.add(origin)

    def __delitem__(self, origin):
        if self.readonly:
            raise TypeError('Published origin data is immutable')
        if origin not in self.origins:
            raise KeyError(origin)
        (self.directory / f'{origin}.npz').unlink(missing_ok=True)
        self.origins.remove(origin)

    def copy(self):
        temporary = TemporaryDirectory(prefix='traffic-origins-')
        result = OriginStore(Path(temporary.name), self.kind, self)
        result.temporary = temporary
        return result
