from collections import namedtuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import (
    Generic,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    MutableMapping,
    NamedTuple,
    TypeVar,
    Union,
)

K = TypeVar("K")
V = TypeVar("V")


@dataclass
class TTLValue(Generic[V]):
    expires_at: datetime
    value: V


class TTLCache(MutableMapping[K, V], Iterable[K]):
    _inner_cache: MutableMapping[K, TTLValue]
    expiration_time: timedelta

    def __init__(self, expiration_time: Union[int, timedelta] = 60) -> None:
        super().__init__()
        if isinstance(expiration_time, int):
            expiration_time = timedelta(seconds=expiration_time)
        else:
            self.expiration_time = expiration_time
        self._inner_cache = {}

    def __contains__(self, k: K) -> bool:
        self.prune_expired()
        return k in self._inner_cache

    def __getitem__(self, k: K) -> V:
        inner = self._inner_cache[k]
        if inner.expires_at < datetime.now():
            del self._inner_cache[k]
            raise KeyError(k)
        return inner.value

    def __setitem__(self, k: K, v: V) -> None:
        self._inner_cache[k] = TTLValue(datetime.now() + self.expiration_time, v)
        self.prune_expired()

    def __delitem__(self, k: K) -> None:
        del self._inner_cache[k]

    def get_expiration(self, k: K) -> datetime:
        return self._inner_cache[k].expires_at

    def prune_expired(self) -> None:
        for k in list(self.keys()):
            if self._inner_cache[k].expires_at < datetime.now():
                del self[k]

    def __len__(self) -> int:
        return len(self._inner_cache)

    def __iter__(self) -> Iterator[K]:
        return iter(self._inner_cache)

    def keys(self) -> KeysView[K]:
        return self._inner_cache.keys()

    def items(self) -> ItemsView[K, TTLValue[V]]:
        return self._inner_cache.items()
