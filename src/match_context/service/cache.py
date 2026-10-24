from collections import OrderedDict
import hashlib
import json
from typing import Generic, TypeVar
from match_context.domain.contracts import ContextRequest

T = TypeVar("T")


class ContextCache(Generic[T]):
    def __init__(self, capacity: int = 128):
        if type(capacity) is not int or not 1 <= capacity <= 128:
            raise ValueError("Cache capacity must be between one and 128")
        self.capacity = capacity
        self._values: OrderedDict[str, T] = OrderedDict()

    @staticmethod
    def key(request: ContextRequest, snapshot_hash: str) -> str:
        payload = {"version": 1, "request": request.model_dump(mode="json"), "snapshot_hash": snapshot_hash}
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def get(self, key: str) -> T | None:
        if key not in self._values:
            return None
        self._values.move_to_end(key)
        return self._values[key]

    def put(self, key: str, value: T) -> None:
        self._values[key] = value
        self._values.move_to_end(key)
        while len(self._values) > self.capacity:
            self._values.popitem(last=False)

    def __len__(self) -> int:
        return len(self._values)
