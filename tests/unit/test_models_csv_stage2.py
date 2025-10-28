"""Unit tests for csv_stage2 models."""

from elsheeto.models.csv_stage2 import HeaderRow, HeaderSection


class TestHeaderRow:
    """Test HeaderRow model and its properties."""

    def test_header_row_creation(self):
        """Test basic HeaderRow creation."""
        row = HeaderRow(key="TestKey", value="TestValue")
        assert row.key == "TestKey"
        assert row.value == "TestValue"

    def test_is_key_value_pair_true(self):
        """Test is_key_value_pair property when both key and value are non-empty."""
        row = HeaderRow(key="IEMFileVersion", value="4")
        assert row.is_key_value_pair is True

    def test_is_key_value_pair_false_empty_key(self):
        """Test is_key_value_pair property when key is empty."""
        row = HeaderRow(key="", value="SomeValue")
        assert row.is_key_value_pair is False

    def test_is_key_value_pair_false_empty_value(self):
        """Test is_key_value_pair property when value is empty."""
        row = HeaderRow(key="SomeKey", value="")
        assert row.is_key_value_pair is False

    def test_is_key_value_pair_false_whitespace_only(self):
        """Test is_key_value_pair property when key/value are whitespace only."""
        row = HeaderRow(key="  ", value="   ")
        assert row.is_key_value_pair is False

    def test_is_key_only_true(self):
        """Test is_key_only property when key exists but value is empty."""
        row = HeaderRow(key="SomeKey", value="")
        assert row.is_key_only is True

    def test_is_key_only_false_both_present(self):
        """Test is_key_only property when both key and value are present."""
        row = HeaderRow(key="SomeKey", value="SomeValue")
        assert row.is_key_only is False

    def test_is_key_only_false_both_empty(self):
        """Test is_key_only property when both key and value are empty."""
        row = HeaderRow(key="", value="")
        assert row.is_key_only is False

    def test_is_key_only_with_whitespace(self):
        """Test is_key_only property with whitespace handling."""
        row = HeaderRow(key="  SomeKey  ", value="   ")
        assert row.is_key_only is True

    def test_is_empty_true(self):
        """Test is_empty property when both key and value are empty."""
        row = HeaderRow(key="", value="")
        assert row.is_empty is True

    def test_is_empty_true_whitespace_only(self):
        """Test is_empty property when both key and value are whitespace only."""
        row = HeaderRow(key="   ", value="  ")
        assert row.is_empty is True

    def test_is_empty_false_key_present(self):
        """Test is_empty property when key is present."""
        row = HeaderRow(key="SomeKey", value="")
        assert row.is_empty is False

    def test_is_empty_false_value_present(self):
        """Test is_empty property when value is present."""
        row = HeaderRow(key="", value="SomeValue")
        assert row.is_empty is False

    def test_is_empty_false_both_present(self):
        """Test is_empty property when both key and value are present."""
        row = HeaderRow(key="SomeKey", value="SomeValue")
        assert row.is_empty is False


class TestHeaderSection:
    """Test HeaderSection model and its properties."""

    def test_header_section_creation(self):
        """Test basic HeaderSection creation."""
        section = HeaderSection(name="header", rows=[])
        assert section.name == "header"
        assert section.rows == []

    def test_key_values_property(self):
        """Test key_values property extracts key-value pairs correctly."""
        rows = [
            HeaderRow(key="IEMFileVersion", value="4"),
            HeaderRow(key="Investigator Name", value="John Doe"),
            HeaderRow(key="EmptyValue", value=""),  # Should be excluded
            HeaderRow(key="", value="EmptyKey"),  # Should be excluded
        ]
        section = HeaderSection(name="header", rows=rows)

        expected = {
            "IEMFileVersion": "4",
            "Investigator Name": "John Doe",
        }
        assert section.key_values == expected
