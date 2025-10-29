from collections import abc
from typing import (
    Any,
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    overload,
)

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


class CaseInsensitiveDict[KT, VT](MutableMapping[KT, VT]):
    """A case-insensitive dictionary that preserves original key casing."""

    @overload
    def __init__(self, data: Mapping[KT, VT] | None = None) -> None: ...

    @overload
    def __init__(self, data: Iterable[tuple[KT, VT]] | None = None) -> None: ...

    def __init__(self, data: Mapping[KT, VT] | Iterable[tuple[KT, VT]] | None = None) -> None:
        # Mapping from lowercased key to tuple of (actual key, value)
        self._data: dict[KT, tuple[KT, VT]] = {}
        if data is None:
            data = {}
        self.update(data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({dict(self.items())!r})"

    @staticmethod
    def _convert_key(key: KT) -> KT:
        if isinstance(key, str):
            return key.lower()  # type: ignore[return-value]
        return key

    def _get_key_value(self, key: KT) -> tuple[KT, VT]:
        try:
            return self._data[self._convert_key(key=key)]
        except KeyError:
            raise KeyError(f"Key: {key!r} not found.") from None

    def __setitem__(self, key: KT, value: VT) -> None:
        self._data[self._convert_key(key=key)] = (key, value)

    def __getitem__(self, key: KT) -> VT:
        return self._get_key_value(key=key)[1]

    def __delitem__(self, key: KT) -> None:
        del self._data[self._convert_key(key=key)]

    def __iter__(self) -> Iterator[KT]:
        return (key for key, _ in self._data.values())

    def __len__(self) -> int:
        return len(self._data)

    def lower_items(self) -> Iterator[tuple[KT, VT]]:
        return ((key, val[1]) for key, val in self._data.items())

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, abc.Mapping):
            return False
        other_dict = CaseInsensitiveDict[Any, Any](data=other)
        return dict(self.lower_items()) == dict(other_dict.lower_items())

    def copy(self) -> "CaseInsensitiveDict[KT, VT]":
        return CaseInsensitiveDict(data=dict(self._data.values()))

    def getkey(self, key: KT) -> KT:
        return self._get_key_value(key=key)[0]

    @classmethod
    def fromkeys(cls, iterable: Iterable[KT], value: VT) -> "CaseInsensitiveDict[KT, VT]":
        return cls([(key, value) for key in iterable])

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        """Generate pydantic core schema for validation."""
        return core_schema.no_info_after_validator_function(
            cls._validate,
            core_schema.dict_schema(
                keys_schema=core_schema.str_schema(),
                values_schema=core_schema.any_schema(),
            ),
        )

    @classmethod
    def _validate(cls, value: Any) -> "CaseInsensitiveDict":
        """Validate and convert value to CaseInsensitiveDict."""
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls(value)
        raise TypeError(f"Expected dict or CaseInsensitiveDict, got {type(value)}")
