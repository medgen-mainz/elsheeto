"""Unit tests for utils module."""

import pytest

from elsheeto.models.utils import CaseInsensitiveDict


class TestCaseInsensitiveDict:
    """Test CaseInsensitiveDict class."""

    def test_init_empty(self):
        """Test creating empty CaseInsensitiveDict."""
        d = CaseInsensitiveDict()
        assert len(d) == 0
        assert dict(d) == {}

    def test_init_with_dict(self):
        """Test creating CaseInsensitiveDict with dictionary."""
        data = {"Key1": "value1", "KEY2": "value2"}
        d = CaseInsensitiveDict(data)
        assert len(d) == 2
        assert d["key1"] == "value1"
        assert d["key2"] == "value2"

    def test_init_with_iterable(self):
        """Test creating CaseInsensitiveDict with iterable of tuples."""
        data = [("Key1", "value1"), ("KEY2", "value2")]
        d = CaseInsensitiveDict(data)
        assert len(d) == 2
        assert d["key1"] == "value1"
        assert d["key2"] == "value2"

    def test_init_with_none(self):
        """Test creating CaseInsensitiveDict with None."""
        d = CaseInsensitiveDict(None)
        assert len(d) == 0
        assert dict(d) == {}

    def test_repr(self):
        """Test string representation."""
        d = CaseInsensitiveDict({"Key": "value"})
        repr_str = repr(d)
        assert "CaseInsensitiveDict" in repr_str
        assert "Key" in repr_str
        assert "value" in repr_str

    def test_convert_key_string(self):
        """Test _convert_key with string."""
        result = CaseInsensitiveDict._convert_key("TEST")
        assert result == "test"

    def test_convert_key_non_string(self):
        """Test _convert_key with non-string."""
        result = CaseInsensitiveDict._convert_key(42)
        assert result == 42

    def test_get_key_value_existing(self):
        """Test _get_key_value with existing key."""
        d = CaseInsensitiveDict({"Key": "value"})
        key, value = d._get_key_value("key")
        assert key == "Key"  # Original case preserved
        assert value == "value"

    def test_get_key_value_missing(self):
        """Test _get_key_value with missing key."""
        d = CaseInsensitiveDict({"Key": "value"})
        with pytest.raises(KeyError, match="Key: 'missing' not found"):
            d._get_key_value("missing")

    def test_setitem_and_getitem(self):
        """Test setting and getting items."""
        d = CaseInsensitiveDict()
        d["Key"] = "value"
        assert d["key"] == "value"
        assert d["KEY"] == "value"
        assert d["Key"] == "value"

    def test_setitem_overwrites_different_case(self):
        """Test that setting with different case overwrites."""
        d = CaseInsensitiveDict()
        d["Key"] = "value1"
        d["KEY"] = "value2"
        assert len(d) == 1
        assert d["key"] == "value2"

    def test_delitem_existing(self):
        """Test deleting existing item."""
        d = CaseInsensitiveDict({"Key": "value"})
        del d["key"]
        assert len(d) == 0
        with pytest.raises(KeyError):
            _ = d["key"]

    def test_delitem_missing(self):
        """Test deleting missing item."""
        d = CaseInsensitiveDict({"Key": "value"})
        with pytest.raises(KeyError):
            del d["missing"]

    def test_iter(self):
        """Test iteration over keys."""
        d = CaseInsensitiveDict({"Key1": "value1", "KEY2": "value2"})
        keys = list(d)
        assert len(keys) == 2
        assert "Key1" in keys or "KEY1" in keys  # Original case preserved
        assert "KEY2" in keys or "key2" in keys  # Original case preserved

    def test_len(self):
        """Test length calculation."""
        d = CaseInsensitiveDict()
        assert len(d) == 0
        d["key1"] = "value1"
        assert len(d) == 1
        d["KEY2"] = "value2"
        assert len(d) == 2

    def test_lower_items(self):
        """Test lower_items method."""
        d = CaseInsensitiveDict({"Key1": "value1", "KEY2": "value2"})
        lower_items = list(d.lower_items())
        assert len(lower_items) == 2
        # Check that keys are lowercase
        for key, _value in lower_items:
            if isinstance(key, str):
                assert key == key.lower()

    def test_eq_with_dict(self):
        """Test equality with regular dict."""
        d1 = CaseInsensitiveDict({"Key": "value"})
        d2 = {"key": "value"}
        assert d1 == d2

    def test_eq_with_case_insensitive_dict(self):
        """Test equality with another CaseInsensitiveDict."""
        d1 = CaseInsensitiveDict({"Key": "value"})
        d2 = CaseInsensitiveDict({"KEY": "value"})
        assert d1 == d2

    def test_eq_with_different_values(self):
        """Test inequality with different values."""
        d1 = CaseInsensitiveDict({"Key": "value1"})
        d2 = {"key": "value2"}
        assert d1 != d2

    def test_eq_with_non_mapping(self):
        """Test equality with non-mapping type."""
        d = CaseInsensitiveDict({"Key": "value"})
        assert d != "not a mapping"
        assert d != 42
        assert d != ["not", "a", "mapping"]

    def test_copy(self):
        """Test copy method."""
        original = CaseInsensitiveDict({"Key": "value"})
        copied = original.copy()
        assert copied == original
        assert copied is not original
        assert isinstance(copied, CaseInsensitiveDict)

        # Modify copy and ensure original is unchanged
        copied["new"] = "value"
        assert "new" not in original

    def test_getkey(self):
        """Test getkey method."""
        d = CaseInsensitiveDict({"Key": "value"})
        assert d.getkey("key") == "Key"  # Returns original case
        assert d.getkey("KEY") == "Key"  # Returns original case

    def test_getkey_missing(self):
        """Test getkey with missing key."""
        d = CaseInsensitiveDict({"Key": "value"})
        with pytest.raises(KeyError, match="Key: 'missing' not found"):
            d.getkey("missing")

    def test_fromkeys(self):
        """Test fromkeys class method."""
        keys = ["key1", "KEY2", "Key3"]
        d = CaseInsensitiveDict.fromkeys(keys, "default")
        assert len(d) == 3
        assert d["key1"] == "default"
        assert d["key2"] == "default"
        assert d["key3"] == "default"

    def test_fromkeys_empty(self):
        """Test fromkeys with empty iterable."""
        d = CaseInsensitiveDict.fromkeys([], "default")
        assert len(d) == 0

    def test_contains(self):
        """Test __contains__ (in operator)."""
        d = CaseInsensitiveDict({"Key": "value"})
        assert "key" in d
        assert "KEY" in d
        assert "Key" in d
        assert "missing" not in d

    def test_get(self):
        """Test get method."""
        d = CaseInsensitiveDict({"Key": "value"})
        assert d.get("key") == "value"
        assert d.get("KEY") == "value"
        assert d.get("missing") is None
        assert d.get("missing", "default") == "default"

    def test_keys(self):
        """Test keys method."""
        d = CaseInsensitiveDict({"Key1": "value1", "KEY2": "value2"})
        keys = list(d.keys())
        assert len(keys) == 2
        # Original case should be preserved
        assert "Key1" in keys or "KEY1" in keys
        assert "KEY2" in keys or "key2" in keys

    def test_values(self):
        """Test values method."""
        d = CaseInsensitiveDict({"Key1": "value1", "KEY2": "value2"})
        values = list(d.values())
        assert len(values) == 2
        assert "value1" in values
        assert "value2" in values

    def test_items(self):
        """Test items method."""
        d = CaseInsensitiveDict({"Key1": "value1", "KEY2": "value2"})
        items = list(d.items())
        assert len(items) == 2
        # Check that we get back the original case keys
        keys = [key for key, _ in items]
        values = [value for _, value in items]
        assert "Key1" in keys or "KEY1" in keys
        assert "KEY2" in keys or "key2" in keys
        assert "value1" in values
        assert "value2" in values

    def test_clear(self):
        """Test clear method."""
        d = CaseInsensitiveDict({"Key1": "value1", "KEY2": "value2"})
        assert len(d) == 2
        d.clear()
        assert len(d) == 0

    def test_pop(self):
        """Test pop method."""
        d = CaseInsensitiveDict({"Key": "value"})
        result = d.pop("key")
        assert result == "value"
        assert len(d) == 0

        # Test with default
        result = d.pop("missing", "default")
        assert result == "default"

        # Test missing without default
        with pytest.raises(KeyError):
            d.pop("missing")

    def test_popitem(self):
        """Test popitem method."""
        d = CaseInsensitiveDict({"Key": "value"})
        key, value = d.popitem()
        assert key == "Key"
        assert value == "value"
        assert len(d) == 0

        # Test on empty dict
        with pytest.raises(KeyError):
            d.popitem()

    def test_setdefault(self):
        """Test setdefault method."""
        d = CaseInsensitiveDict({"Key": "value"})

        # Existing key
        result = d.setdefault("key", "new_value")
        assert result == "value"
        assert d["key"] == "value"

        # New key
        result = d.setdefault("new_key", "new_value")
        assert result == "new_value"
        assert d["new_key"] == "new_value"

    def test_update_with_dict(self):
        """Test update with dictionary."""
        d = CaseInsensitiveDict({"Key1": "value1"})
        d.update({"KEY2": "value2", "key3": "value3"})
        assert len(d) == 3
        assert d["key1"] == "value1"
        assert d["key2"] == "value2"
        assert d["key3"] == "value3"

    def test_update_with_iterable(self):
        """Test update with iterable of tuples."""
        d = CaseInsensitiveDict({"Key1": "value1"})
        d.update([("KEY2", "value2"), ("key3", "value3")])
        assert len(d) == 3
        assert d["key1"] == "value1"
        assert d["key2"] == "value2"
        assert d["key3"] == "value3"

    def test_update_with_kwargs(self):
        """Test update with keyword arguments."""
        d = CaseInsensitiveDict({"Key1": "value1"})
        d.update(key2="value2", key3="value3")
        assert len(d) == 3
        assert d["key1"] == "value1"
        assert d["key2"] == "value2"
        assert d["key3"] == "value3"

    def test_pydantic_validation_with_dict(self):
        """Test pydantic validation with regular dict."""
        result = CaseInsensitiveDict._validate({"Key": "value"})
        assert isinstance(result, CaseInsensitiveDict)
        assert result["key"] == "value"

    def test_pydantic_validation_with_case_insensitive_dict(self):
        """Test pydantic validation with CaseInsensitiveDict."""
        original = CaseInsensitiveDict({"Key": "value"})
        result = CaseInsensitiveDict._validate(original)
        assert result is original

    def test_pydantic_validation_with_invalid_type(self):
        """Test pydantic validation with invalid type."""
        with pytest.raises(TypeError, match="Expected dict or CaseInsensitiveDict, got"):
            CaseInsensitiveDict._validate("not a dict")

    def test_mixed_string_and_non_string_keys(self):
        """Test dictionary with mixed key types."""
        d = CaseInsensitiveDict()
        d["String"] = "string_value"
        d[42] = "int_value"
        d[("tuple", "key")] = "tuple_value"

        assert len(d) == 3
        assert d["string"] == "string_value"  # Case insensitive for strings
        assert d[42] == "int_value"  # Exact match for non-strings
        assert d[("tuple", "key")] == "tuple_value"  # Exact match for non-strings

    def test_preserve_original_case_with_multiple_operations(self):
        """Test that original case is preserved through multiple operations."""
        d = CaseInsensitiveDict()
        d["CamelCase"] = "value1"
        d["UPPER"] = "value2"
        d["lower"] = "value3"

        # Access with different cases
        assert d["camelcase"] == "value1"
        assert d["upper"] == "value2"
        assert d["LOWER"] == "value3"

        # Check that original case is preserved in keys
        keys = list(d.keys())
        assert "CamelCase" in keys
        assert "UPPER" in keys
        assert "lower" in keys

    def test_pydantic_serialization(self):
        """Test Pydantic serialization works without warnings."""
        from pydantic import BaseModel

        class TestModel(BaseModel):
            data: CaseInsensitiveDict[str, str]

        # Create test data
        test_dict = CaseInsensitiveDict({"Key1": "value1", "KEY2": "value2"})
        model = TestModel(data=test_dict)

        # Test serialization
        serialized = model.model_dump()
        assert isinstance(serialized["data"], dict)
        assert serialized["data"]["Key1"] == "value1"
        assert serialized["data"]["KEY2"] == "value2"

        # Test JSON serialization
        json_str = model.model_dump_json()
        assert "Key1" in json_str
        assert "value1" in json_str
