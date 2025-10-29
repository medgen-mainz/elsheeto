from __future__ import annotations

from collections import abc
from typing import (
    Any,
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    TypeVar,
    overload,
)

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

#: Type variable for key types in `CaseInsensitiveDict`.
_KT = TypeVar("_KT")
#: Type variable for value types in `CaseInsensitiveDict`.
_VT = TypeVar("_VT")


class CaseInsensitiveDict[_KT, _VT](MutableMapping[_KT, _VT]):
    """A case-insensitive dictionary that preserves original key casing."""

    @overload
    def __init__(self, data: Mapping[_KT, _VT] | None = None) -> None: ...

    @overload
    def __init__(self, data: Iterable[tuple[_KT, _VT]] | None = None) -> None: ...

    def __init__(self, data: Mapping[_KT, _VT] | Iterable[tuple[_KT, _VT]] | None = None) -> None:
        # Mapping from lowercased key to tuple of (actual key, value)
        self._data: dict[_KT, tuple[_KT, _VT]] = {}
        if data is None:
            data = {}
        self.update(data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({dict(self.items())!r})"

    @staticmethod
    def _convert_key(key: _KT) -> _KT:
        if isinstance(key, str):
            return key.lower()  # type: ignore[return-value]
        return key

    def _get_key_value(self, key: _KT) -> tuple[_KT, _VT]:
        try:
            return self._data[self._convert_key(key=key)]
        except KeyError:
            raise KeyError(f"Key: {key!r} not found.") from None

    def __setitem__(self, key: _KT, value: _VT) -> None:
        self._data[self._convert_key(key=key)] = (key, value)

    def __getitem__(self, key: _KT) -> _VT:
        return self._get_key_value(key=key)[1]

    def __delitem__(self, key: _KT) -> None:
        del self._data[self._convert_key(key=key)]

    def __iter__(self) -> Iterator[_KT]:
        return (key for key, _ in self._data.values())

    def __len__(self) -> int:
        return len(self._data)

    def lower_items(self) -> Iterator[tuple[_KT, _VT]]:
        return ((key, val[1]) for key, val in self._data.items())

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, abc.Mapping):
            return False
        other_dict = CaseInsensitiveDict[Any, Any](data=other)
        return dict(self.lower_items()) == dict(other_dict.lower_items())

    def copy(self) -> "CaseInsensitiveDict[_KT, _VT]":
        return CaseInsensitiveDict(data=dict(self._data.values()))

    def getkey(self, key: _KT) -> _KT:
        return self._get_key_value(key=key)[0]

    @classmethod
    def fromkeys(cls, iterable: Iterable[_KT], value: _VT) -> "CaseInsensitiveDict[_KT, _VT]":
        return cls([(key, value) for key in iterable])

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        """Generate pydantic core schema for validation and serialization."""
        return core_schema.no_info_before_validator_function(
            cls._validate,
            core_schema.dict_schema(
                keys_schema=core_schema.str_schema(),
                values_schema=core_schema.any_schema(),
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls._serialize,
                return_schema=core_schema.dict_schema(
                    keys_schema=core_schema.str_schema(),
                    values_schema=core_schema.any_schema(),
                ),
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

    @classmethod
    def _serialize(cls, value: "CaseInsensitiveDict") -> dict[str, Any]:
        """Serialize CaseInsensitiveDict to regular dict for Pydantic."""
        return dict(value.items())
