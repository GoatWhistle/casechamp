from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.sparse import csr_matrix

from app.domain.errors import InvalidQuery


@dataclass(frozen=True)
class WeightedRoads:
    hours: Any
    key: str

    def validate(self, count: int) -> None:
        if len(self.hours) != count or np.any(np.isnan(self.hours)) or np.any(self.hours < 0):
            raise InvalidQuery(
                "Weighted road costs must match the graph and be nonnegative hours without NaN"
            )


def minimum_csr(src: Any, dst: Any, weights: Any, count: int, directed: bool = False) -> Any:
    a = np.asarray(src, dtype=np.int64) if directed else np.concatenate([src, dst]).astype(np.int64)
    b = np.asarray(dst, dtype=np.int64) if directed else np.concatenate([dst, src]).astype(np.int64)
    keys = a * count + b
    w = np.asarray(weights) if directed else np.concatenate([weights, weights])
    order = np.argsort(keys, kind="stable")
    keys = keys[order]
    if len(keys):
        starts = np.flatnonzero(np.r_[True, keys[1:] != keys[:-1]])
        values = np.minimum.reduceat(w[order], starts).astype(np.float64)
        keys = keys[starts]
    else:
        values = np.empty(0, dtype=np.float64)
    rows = keys // count
    indptr = np.zeros(count + 1, dtype=np.int64)
    np.cumsum(np.bincount(rows, minlength=count), out=indptr[1:])
    return csr_matrix(
        (values, (keys % count).astype(np.int32), indptr.astype(np.int32)), shape=(count, count)
    )
