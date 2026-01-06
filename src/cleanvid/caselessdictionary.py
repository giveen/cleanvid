from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple


class CaselessDictionary(dict):
    """Dictionary that enables case insensitive searching while preserving case sensitivity
when keys are listed, ie, via keys() or items() methods.

Works by storing a lowercase version of the key as the new key and stores the original key-value
pair as the key's value (values become dictionaries)."""

    def __init__(self, initval: Optional[Iterable[Tuple[str, Any]]] = None) -> None:
        if initval is None:
            return
        if isinstance(initval, dict):
            for key, value in initval.items():
                self.__setitem__(key, value)
        else:
            for (key, value) in initval:
                self.__setitem__(key, value)

    def __repr__(self):
        ans = dict()
        for key, val in self.items():
            ans[key] = val
        return str(ans)

    # __str__ for print()
    def __str__(self):
        return self.__repr__()

    def __contains__(self, key: object) -> bool:
        try:
            return dict.__contains__(self, str(key).lower())
        except Exception:
            return False

    def __getitem__(self, key: str) -> Any:
        return dict.__getitem__(self, key.lower())['val']

    def __setitem__(self, key: str, value: Any) -> None:
        try:
            return dict.__setitem__(self, key.lower(), {'key': key, 'val': value})
        except Exception:
            return dict.__setitem__(self, key, {'key': key, 'val': value})

    def get(self, key: object, default: Any = None) -> Any:
        try:
            return dict.__getitem__(self, str(key).lower())['val']
        except Exception:
            return default

    def has_key(self, key: object) -> bool:
        return key in self

    def items(self) -> Iterator[Tuple[str, Any]]:
        for v in dict.values(self):
            yield (v['key'], v['val'])

    def keys(self) -> Iterator[str]:
        for v in dict.values(self):
            yield v['key']

    def values(self) -> Iterator[Any]:
        for v in dict.values(self):
            yield v['val']

    def printable(self, sep: str = ', ', key=None) -> str:
        if key is None:
            key = self.keys
        try:
            return sep.join(key())
        except TypeError:
            ans = ''
            for v in key():
                ans += str(v)
                ans += sep
            return ans[:-len(sep)]
