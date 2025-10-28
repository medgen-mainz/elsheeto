"""Unit tests for csv_stage2 models."""

from elsheeto.models.csv_stage2 import HeaderSection


class TestHeaderSection:
    """Test HeaderSection model and its properties."""

    def test_header_section_creation(self):
        """Test basic HeaderSection creation."""
        section = HeaderSection(name="header", rows=[])
        assert section.name == "header"
        assert section.rows == []

    def test_header_section_with_rows(self):
        """Test HeaderSection creation with rows."""
        rows = [
            ["IEMFileVersion", "4"],
            ["Investigator Name", "John Doe"],
            ["151"],  # Single value row
        ]
        section = HeaderSection(name="header", rows=rows)
        assert section.name == "header"
        assert section.rows == rows

    def test_key_values_property_two_column_rows(self):
        """Test key_values property extracts key-value pairs correctly from 2-column rows."""
        rows = [
            ["IEMFileVersion", "4"],
            ["Investigator Name", "John Doe"],
            ["EmptyValue", ""],  # Should be excluded (empty value)
            ["", "EmptyKey"],  # Should be excluded (empty key)
            ["151"],  # Should be excluded (not 2 non-empty cells)
            ["Setting", "Value", "Lane"],  # Should be excluded (3 non-empty cells)
        ]
        section = HeaderSection(name="header", rows=rows)

        expected = {
            "IEMFileVersion": "4",
            "Investigator Name": "John Doe",
        }
        assert section.key_values == expected

    def test_key_values_property_empty_section(self):
        """Test key_values property with empty section."""
        section = HeaderSection(name="header", rows=[])
        assert section.key_values == {}

    def test_key_values_property_no_valid_pairs(self):
        """Test key_values property when no rows form valid key-value pairs."""
        rows = [
            ["151"],  # Single value
            ["Setting", "Value", "Lane"],  # Three values
            ["", ""],  # Empty row
        ]
        section = HeaderSection(name="header", rows=rows)
        assert section.key_values == {}

    def test_key_values_property_with_whitespace(self):
        """Test key_values property handles whitespace correctly."""
        rows = [
            ["  IEMFileVersion  ", "  4  "],
            ["Investigator Name", "John Doe"],
            ["  ", "  "],  # Should be excluded (whitespace only)
        ]
        section = HeaderSection(name="header", rows=rows)

        expected = {
            "IEMFileVersion": "4",
            "Investigator Name": "John Doe",
        }
        assert section.key_values == expected
