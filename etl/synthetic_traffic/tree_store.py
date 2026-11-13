from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from numpy.typing import NDArray


@dataclass
class Tree:
    distance: NDArray[np.float64]
    parent: NDArray[np.int64]
    limit: float = float("inf")


class TreeStore(MutableMapping):
    def __init__(self, directory: Path, base: Mapping | None = None):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.base = base if base is not None else {}
        self.origins = set(self.base) | {int(path.stem) for path in directory.glob('*.npz')}
        self.temporary = None

    def __iter__(self):
        return iter(sorted(self.origins))

    def __len__(self):
        return len(self.origins)

    def __getitem__(self, origin):
        if origin not in self.origins:
            raise KeyError(origin)
        path = self.directory / f'{origin}.npz'
        if path.exists():
            with np.load(path, allow_pickle=False) as arrays:
                return Tree(arrays['distance'], arrays['parent'], float(arrays['limit']) if 'limit' in arrays else np.inf)
        return self.base[origin]

    def __setitem__(self, origin, tree):
        path = self.directory / f'{origin}.npz'
        staging = path.with_suffix('.tmp')
        with staging.open('wb') as stream:
            np.savez_compressed(stream, distance=tree.distance, parent=tree.parent, limit=tree.limit)
        staging.replace(path)
        self.origins.add(origin)

    def __delitem__(self, origin):
        if origin not in self.origins:
            raise KeyError(origin)
        (self.directory / f'{origin}.npz').unlink(missing_ok=True)
        self.origins.remove(origin)

    def fork(self):
        temporary = TemporaryDirectory(prefix='traffic-trees-', dir=self.directory.parent)
        result = TreeStore(Path(temporary.name), self)
        result.temporary = temporary
        return result


class ArchiveTrees(Mapping):
    def __init__(self, path: Path, origins):
        self.path = path
        self.origins = set(map(int, origins))

    def __len__(self):
        return len(self.origins)

    def __iter__(self):
        return iter(sorted(self.origins))

    def __getitem__(self, origin):
        if origin not in self.origins:
            raise KeyError(origin)
        with np.load(self.path, allow_pickle=False) as arrays:
            return Tree(arrays[f'distance_{origin}'], arrays[f'parent_{origin}'],
                        float(arrays[f'limit_{origin}']) if f'limit_{origin}' in arrays else np.inf)

    def fork(self):
        temporary = TemporaryDirectory(prefix='traffic-trees-')
        result = TreeStore(Path(temporary.name), self)
        result.temporary = temporary
        return result
