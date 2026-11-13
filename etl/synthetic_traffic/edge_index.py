from collections.abc import Iterator, Mapping

import numpy as np
from scipy.sparse import csr_matrix


class EdgeIndex(Mapping):
    def __init__(self, keys, weights, indices, size):
        self.keys_array = keys
        self.weights = weights
        self.indices = indices
        self.size = size

    def __len__(self):
        return len(self.keys_array)

    def __iter__(self) -> Iterator[tuple[int, int]]:
        for key in self.keys_array:
            yield divmod(int(key), self.size)

    def __getitem__(self, pair):
        u, v = pair
        key = u * self.size + v
        location = int(np.searchsorted(self.keys_array, key))
        if location >= len(self) or self.keys_array[location] != key:
            raise KeyError(pair)
        return float(self.weights[location]), int(self.indices[location])

    def edge_ids(self, pairs):
        keys = np.fromiter((u * self.size + v for u, v in pairs), dtype=np.int64)
        positions = np.searchsorted(self.keys_array, keys)
        present = positions < len(self)
        present[present] &= self.keys_array[positions[present]] == keys[present]
        if not np.all(present):
            raise KeyError(divmod(int(keys[np.flatnonzero(~present)[0]]), self.size))
        return self.indices[positions]

    def changed(self, other):
        if self.size != other.size:
            raise ValueError('Edge indexes must preserve node count')
        keys = np.union1d(self.keys_array, other.keys_array)
        old = np.searchsorted(self.keys_array, keys)
        new = np.searchsorted(other.keys_array, keys)
        present_old = old < len(self)
        present_new = new < len(other)
        present_old[present_old] &= self.keys_array[old[present_old]] == keys[present_old]
        present_new[present_new] &= other.keys_array[new[present_new]] == keys[present_new]
        both = present_old & present_new
        changed = ~both
        changed[both] = (self.weights[old[both]] != other.weights[new[both]]) | (
            self.indices[old[both]] != other.indices[new[both]])
        return {divmod(int(key), self.size) for key in keys[changed]}

    def graph(self):
        return csr_matrix((self.weights, (self.keys_array // self.size,
                                          self.keys_array % self.size)),
                            shape=(self.size, self.size))
    def adjacency(self):
        matrix = self.graph()
        return Neighbors(matrix.T.tocsr()), Neighbors(matrix)


class Neighbors:
    def __init__(self, matrix):
        self.matrix = matrix

    def get(self, node, default=()):
        start, end = self.matrix.indptr[node:node + 2]
        return zip(self.matrix.indices[start:end], self.matrix.data[start:end], strict=True)
