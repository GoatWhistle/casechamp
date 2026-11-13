from typing import Literal

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(extra="forbid"))
class TrafficData:
    kind: Literal["traffic_data"]
