from typing import Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


class CaseInsensitiveDict(dict[str, Any]):
    """A case-insensitive dictionary that preserves original key casing."""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        """Initialize with optional data."""
        super().__init__()
        self._keys: dict[str, str] = {}  # lowercase -> original case mapping
        if data:
            self.update(data)

    def __setitem__(self, key: str, value: Any) -> None:
        """Set item with case-insensitive key."""
        lower_key = key.lower()
        if lower_key in self._keys:
            # Remove old entry with different casing
            super().__delitem__(self._keys[lower_key])
        self._keys[lower_key] = key
        super().__setitem__(key, value)

    def __getitem__(self, key: str) -> Any:
        """Get item with case-insensitive key."""
        lower_key = key.lower()
        if lower_key in self._keys:
            return super().__getitem__(self._keys[lower_key])
        raise KeyError(key)

    def __delitem__(self, key: str) -> None:
        """Delete item with case-insensitive key."""
        lower_key = key.lower()
        if lower_key in self._keys:
            original_key = self._keys[lower_key]
            del self._keys[lower_key]
            super().__delitem__(original_key)
        else:
            raise KeyError(key)

    def __contains__(self, key: object) -> bool:
        """Check if key exists (case-insensitive)."""
        if isinstance(key, str):
            return key.lower() in self._keys
        return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get item with case-insensitive key, return default if not found."""
        try:
            return self[key]
        except KeyError:
            return default

    def update(self, other: dict[str, Any] | None = None, **kwargs: Any) -> None:
        """Update with another dictionary."""
        if other is not None:
            for key, value in other.items():
                self[key] = value
        for key, value in kwargs.items():
            self[key] = value

    def keys(self):  # type: ignore[override]
        """Return original case keys."""
        return super().keys()

    def items(self):  # type: ignore[override]
        """Return items with original case keys."""
        return super().items()

    def values(self):  # type: ignore[override]
        """Return values."""
        return super().values()

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
