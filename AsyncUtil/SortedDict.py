from collections.abc import MutableMapping
from typing import Dict, Iterator, List, Mapping, Optional, Tuple, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class SortedDict(MutableMapping, Mapping[K, V]):  # type: ignore
    _items: List[Tuple[K, V]]

    def __init__(self, defaults: Optional[Dict[K, V]] = None) -> None:
        self._items = []

        for k, v in (defaults or {}).items():
            self[k] = v

    def __contains__(self, key: object) -> bool:
        min = 0
        max = len(self)

        if max == 0:
            return False
        max -= 1

        while min <= max:
            idx = int((max + min) / 2)
            idx_k = self._items[idx][0]
            if idx_k < key:  # type: ignore
                min = idx + 1
            elif idx_k > key:  # type: ignore
                max = idx - 1
            else:
                return True
        return False

    def __iter__(self) -> Iterator[K]:
        for item in self._items:
            yield item[0]

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, key: K) -> V:
        min = 0
        max = len(self)

        if max == 0:
            raise KeyError

        while min <= max:
            idx = int((max + min) / 2)
            item = self._items[idx]
            if item[0] < key:  # type: ignore
                min = idx + 1
            elif item[0] > key:  # type: ignore
                max = idx - 1
            else:
                return item[1]
        raise KeyError

    def __setitem__(self, key: K, val: V) -> None:
        min = 0
        max = len(self)

        if max == 0:
            self._items.append((key, val))
            return
        max -= 1

        while min <= max:
            idx = int((max + min) / 2)
            idx_k = self._items[idx][0]
            if idx_k < key:  # type: ignore
                min = idx + 1
            elif idx_k > key:  # type: ignore
                max = idx - 1
            else:
                self._items[idx] = (key, val)
                return
        self._items.insert(min, (key, val))

    def __delitem__(self, key: K) -> None:
        min = 0
        max = len(self)

        if max == 0:
            raise KeyError
        max -= 1

        while min <= max:
            idx = int((max + min) / 2)
            idx_k = self._items[idx][0]
            if idx_k < key:  # type: ignore
                min = idx + 1
            elif idx_k > key:  # type: ignore
                max = idx - 1
            else:
                del self._items[idx]
                return
        raise KeyError

    def __repr__(self) -> str:
        out = "SortedDict({"
        for k, v, in self.items():
            out += f"{k.__repr__()}: {v.__repr__()}, "
        return out[:-2] + "})"
