"""Unit tests for stage1 parser."""

import pathlib
import pytest

from elsheeto.models.csv_stage1 import ParsedRawSheet, ParsedRawType
from elsheeto.parser.common import (
    CaseConsistency,
    ColumnConsistency,
    CsvDelimiter,
    ParserConfiguration,
)
from elsheeto.parser.stage1 import Parser, parse


class TestParser:
    """Test cases for the Parser class."""

    def test_init(self):
        """Test Parser initialization."""
        config = ParserConfiguration()
        parser = Parser(config)
        assert parser.config == config

    def test_parse_sectioned_illumina_style(self):
        """Test parsing Illumina-style sectioned CSV."""
        data = """[Header],,,,
IEMFileVersion,5,,,
Experiment Name,MyExperimentName,,,
,,,,
[Data],,,,
Sample_ID,Sample_Name,Sample_Plate,Sample_Well
L11-00001_01,,TestPlate,A01
L11-00002_01,,TestPlate,B01
"""
        config = ParserConfiguration()
        parser = Parser(config)
        result = parser.parse(data=data)

        assert result.delimiter == ","
        assert result.sheet_type == ParsedRawType.SECTIONED
        assert len(result.sections) == 2

        # Check Header section
        header_section = result.sections[0]
        assert header_section.name == "header"
        assert header_section.num_columns == 5
        assert len(header_section.data) == 2  # Two non-empty rows
        assert header_section.data[0] == ["IEMFileVersion", "5", "", "", ""]

        # Check Data section
        data_section = result.sections[1]
        assert data_section.name == "data"
        assert data_section.num_columns == 4
        assert len(data_section.data) == 3  # Header + 2 data rows
        assert data_section.data[0] == ["Sample_ID", "Sample_Name", "Sample_Plate", "Sample_Well"]

    def test_parse_sectioned_aviti_style(self):
        """Test parsing Aviti-style sectioned CSV."""
        data = """[Samples],,,
SampleName,Index1,Index2,Lane
Sample_1,CCC,AAA,1
Sample_2,TTT,GGG,1
"""
        config = ParserConfiguration()
        parser = Parser(config)
        result = parser.parse(data=data)

        assert result.delimiter == ","
        assert result.sheet_type == ParsedRawType.SECTIONED
        assert len(result.sections) == 1

        samples_section = result.sections[0]
        assert samples_section.name == "samples"
        assert samples_section.num_columns == 4
        assert len(samples_section.data) == 3  # Header + 2 data rows

    def test_parse_sectionless(self):
        """Test parsing sectionless CSV."""
        data = """Sample_ID,Sample_Name,Project
S1,Sample1,Proj1
S2,Sample2,Proj1
"""
        config = ParserConfiguration()
        parser = Parser(config)
        result = parser.parse(data=data)

        assert result.delimiter == ","
        assert result.sheet_type == ParsedRawType.SECTIONLESS
        assert len(result.sections) == 1

        section = result.sections[0]
        assert section.name == ""
        assert section.num_columns == 3
        assert len(section.data) == 3

    def test_parse_empty_data(self):
        """Test parsing empty data."""
        data = ""
        config = ParserConfiguration()
        parser = Parser(config)
        result = parser.parse(data=data)

        assert len(result.sections) == 1
        assert result.sections[0].name == ""
        assert result.sections[0].num_columns == 0
        assert result.sections[0].data == []

    def test_parse_with_comments(self):
        """Test parsing with comment lines."""
        data = """# This is a comment
[Header]
# Another comment
Key,Value
TestKey,TestValue
# Final comment
"""
        config = ParserConfiguration()
        parser = Parser(config)
        result = parser.parse(data=data)

        assert len(result.sections) == 1
        header_section = result.sections[0]
        assert header_section.name == "header"
        assert len(header_section.data) == 2  # Key,Value and TestKey,TestValue

    def test_parse_with_empty_lines(self):
        """Test parsing with empty lines."""
        data = """
[Header]

Key,Value

TestKey,TestValue

"""
        config = ParserConfiguration()
        parser = Parser(config)
        result = parser.parse(data=data)

        assert len(result.sections) == 1
        header_section = result.sections[0]
        assert header_section.name == "header"
        assert len(header_section.data) == 2

    def test_parse_without_ignoring_empty_lines(self):
        """Test parsing without ignoring empty lines."""
        data = """[Header]

Key,Value
"""
        config = ParserConfiguration(ignore_empty_lines=False)
        parser = Parser(config)
        result = parser.parse(data=data)

        header_section = result.sections[0]
        assert len(header_section.data) == 2  # Empty row and Key,Value row

    def test_case_sensitivity_section_headers(self):
        """Test case sensitivity for section headers."""
        data = """[HEADER]
Key,Value
TestKey,TestValue
"""
        # Case insensitive (default)
        config = ParserConfiguration()
        parser = Parser(config)
        result = parser.parse(data=data)
        assert result.sections[0].name == "header"

        # Case sensitive
        config = ParserConfiguration(section_header_case=CaseConsistency.CASE_SENSITIVE)
        parser = Parser(config)
        result = parser.parse(data=data)
        assert result.sections[0].name == "HEADER"

    def test_custom_comment_prefixes(self):
        """Test custom comment prefixes."""
        data = """// This is a comment
[Header]
;; Another comment style
Key,Value
TestKey,TestValue
"""
        config = ParserConfiguration(comment_prefixes=["//", ";;"])
        parser = Parser(config)
        result = parser.parse(data=data)

        header_section = result.sections[0]
        assert len(header_section.data) == 2  # Only Key,Value and TestKey,TestValue

    def test_different_delimiters(self):
        """Test parsing with different delimiters."""
        # Tab-separated
        tab_data = "[Header]\nKey\tValue\nTestKey\tTestValue"
        config = ParserConfiguration()
        parser = Parser(config)
        result = parser.parse(data=tab_data)
        assert result.delimiter == "\t"

        # Semicolon-separated
        semicolon_data = "[Header]\nKey;Value\nTestKey;TestValue"
        result = parser.parse(data=semicolon_data)
        assert result.delimiter == ";"

    def test_column_consistency_strict_sectioned(self):
        """Test strict sectioned column consistency."""
        data = """[Section1]
A,B,C
1,2,3
4,5  # This row has only 2 columns
"""
        config = ParserConfiguration(column_consistency=ColumnConsistency.STRICT_SECTIONED)
        parser = Parser(config)

        with pytest.raises(ValueError, match="Section 'section1' column consistency violated"):
            parser.parse(data=data)

    def test_column_consistency_strict_global(self):
        """Test strict global column consistency."""
        data = """[Section1]
A,B,C
1,2,3

[Section2]
X,Y  # This section has only 2 columns
7,8
"""
        config = ParserConfiguration(column_consistency=ColumnConsistency.STRICT_GLOBAL)
        parser = Parser(config)

        with pytest.raises(ValueError, match="Global column consistency violated"):
            parser.parse(data=data)

    def test_column_consistency_loose(self):
        """Test loose column consistency (no validation)."""
        data = """[Section1]
A,B,C
1,2,3
4,5

[Section2]
X,Y
7,8
"""
        config = ParserConfiguration(column_consistency=ColumnConsistency.LOOSE)
        parser = Parser(config)
        result = parser.parse(data=data)

        # Should parse without errors
        assert len(result.sections) == 2
        assert result.sections[0].num_columns == 3
        assert result.sections[1].num_columns == 2

    def test_is_empty_row(self):
        """Test empty row detection."""
        config = ParserConfiguration()
        parser = Parser(config)

        assert parser._is_empty_row(["", "", ""])
        assert parser._is_empty_row(["  ", "  ", "  "])
        assert not parser._is_empty_row(["", "data", ""])
        assert not parser._is_empty_row(["data"])

    def test_is_comment_row(self):
        """Test comment row detection."""
        config = ParserConfiguration()
        parser = Parser(config)

        assert parser._is_comment_row(["# comment"])
        assert parser._is_comment_row(["  # comment with leading spaces"])
        assert not parser._is_comment_row(["data"])
        assert not parser._is_comment_row([""])

    def test_extract_section_name(self):
        """Test section name extraction."""
        config = ParserConfiguration()
        parser = Parser(config)

        assert parser._extract_section_name(["[Header]"]) == "header"
        assert parser._extract_section_name(["  [Data]  "]) == "data"
        assert parser._extract_section_name(["[Settings]", "extra", "columns"]) == "settings"
        assert parser._extract_section_name(["not a section"]) is None
        assert parser._extract_section_name(["[incomplete"]) is None
        assert parser._extract_section_name([""]) is None

    def test_extract_section_name_case_sensitive(self):
        """Test section name extraction with case sensitivity."""
        config = ParserConfiguration(section_header_case=CaseConsistency.CASE_SENSITIVE)
        parser = Parser(config)

        assert parser._extract_section_name(["[Header]"]) == "Header"
        assert parser._extract_section_name(["[DATA]"]) == "DATA"

    def test_create_section(self):
        """Test section creation."""
        config = ParserConfiguration()
        parser = Parser(config)

        data = [["A", "B"], ["1", "2"], ["3", "4"]]
        section = parser._create_section("test", data)

        assert section.name == "test"
        assert section.num_columns == 2
        assert section.data == data

        # Empty data
        empty_section = parser._create_section("empty", [])
        assert empty_section.num_columns == 0
        assert empty_section.data == []

    def test_quoted_fields(self):
        """Test parsing CSV with quoted fields."""
        data = '''[Header]
"Field 1","Field, 2","Field ""3"""
"Value 1","Value, 2","Value ""3"""
'''
        config = ParserConfiguration()
        parser = Parser(config)
        result = parser.parse(data=data)

        header_section = result.sections[0]
        assert header_section.data[0] == ["Field 1", "Field, 2", 'Field "3"']
        assert header_section.data[1] == ["Value 1", "Value, 2", 'Value "3"']


def _get_test_csv_files():
    """Get all CSV files from the test data directory.
    
    Returns:
        List of pathlib.Path objects for all CSV files in tests/data/*/*.csv
    """
    test_data_dir = pathlib.Path(__file__).parent.parent / "data"
    csv_files = []
    
    # Find all CSV files in subdirectories
    for subdir in test_data_dir.iterdir():
        if subdir.is_dir():
            for csv_file in subdir.glob("*.csv"):
                csv_files.append(csv_file)
    
    return sorted(csv_files)


def _get_test_configurations():
    """Get various parser configurations for smoke testing.
    
    Returns:
        List of tuples (config_name, ParserConfiguration) for testing.
    """
    return [
        ("default", ParserConfiguration()),
        ("case_sensitive", ParserConfiguration(
            section_header_case=CaseConsistency.CASE_SENSITIVE,
            column_header_case=CaseConsistency.CASE_SENSITIVE,
            key_case=CaseConsistency.CASE_SENSITIVE,
        )),
        ("loose_columns", ParserConfiguration(
            column_consistency=ColumnConsistency.LOOSE,
        )),
        ("strict_global", ParserConfiguration(
            column_consistency=ColumnConsistency.STRICT_GLOBAL,
        )),
        ("no_empty_line_ignore", ParserConfiguration(
            ignore_empty_lines=False,
        )),
        ("comma_delimiter", ParserConfiguration(
            delimiter=CsvDelimiter.COMMA,
        )),
        ("tab_delimiter", ParserConfiguration(
            delimiter=CsvDelimiter.TAB,
        )),
        ("semicolon_delimiter", ParserConfiguration(
            delimiter=CsvDelimiter.SEMICOLON,
        )),
        ("custom_comments", ParserConfiguration(
            comment_prefixes=["#", "//", ";"],
        )),
    ]


@pytest.mark.parametrize("csv_file", _get_test_csv_files(), ids=lambda p: f"{p.parent.name}/{p.name}")
@pytest.mark.parametrize("config_name,config", _get_test_configurations(), ids=lambda x: x[0] if isinstance(x, tuple) else str(x))
class TestSmokeTests:
    """Smoke tests running all test CSV files with various configurations."""

    def test_parse_smoke(self, csv_file: pathlib.Path, config_name: str, config: ParserConfiguration):
        """Smoke test parsing all CSV files with various configurations.
        
        This test ensures that:
        1. The parser doesn't crash on any of the test files
        2. The parser returns a valid ParsedRawSheet
        3. Basic structural properties are maintained
        
        Args:
            csv_file: Path to the CSV file to test.
            config_name: Name of the configuration being tested.
            config: Parser configuration to use.
        """
        # Read the test file
        with open(csv_file, 'r', encoding='utf-8') as f:
            data = f.read()
        
        try:
            # Parse with the given configuration
            parser = Parser(config)
            result = parser.parse(data=data)
            
            # Basic validation that we got a valid result
            assert isinstance(result, ParsedRawSheet)
            assert result.delimiter in [",", "\t", ";"]  # Should be one of the supported delimiters
            assert result.sheet_type in [ParsedRawType.SECTIONED, ParsedRawType.SECTIONLESS]
            assert isinstance(result.sections, list)
            assert len(result.sections) >= 1  # Should have at least one section
            
            # Validate each section
            for section in result.sections:
                assert isinstance(section.name, str)
                assert isinstance(section.num_columns, int)
                assert section.num_columns >= 0
                assert isinstance(section.data, list)
                
                # If there's data, num_columns should be the max row length
                if section.data:
                    max_cols = max(len(row) for row in section.data) if section.data else 0
                    assert section.num_columns == max_cols
            
            # Additional validation based on file type
            if "illumina" in str(csv_file):
                # Illumina files should typically be sectioned
                assert result.sheet_type == ParsedRawType.SECTIONED
                # Should have multiple sections (Header, Data, etc.)
                assert len(result.sections) >= 1
                
            elif "aviti" in str(csv_file):
                # Aviti files should typically be sectioned
                assert result.sheet_type == ParsedRawType.SECTIONED
                # Should have at least a Samples section
                section_names = [s.name.lower() for s in result.sections]
                assert any("sample" in name for name in section_names)
        
        except ValueError as e:
            # Some configurations may legitimately fail with certain files
            # (e.g., strict column consistency with inconsistent data)
            # We allow these to fail but log them for awareness
            if "column consistency violated" in str(e):
                pytest.skip(f"Expected failure with {config_name} on {csv_file.name}: {e}")
            else:
                # Re-raise unexpected ValueError
                raise
        
        except Exception as e:
            # Any other exception is a real failure
            pytest.fail(f"Unexpected error with {config_name} on {csv_file.name}: {e}")


class TestParseFunction:
    """Test cases for the parse function."""

    def test_parse_function(self):
        """Test the standalone parse function."""
        data = """[Header]
Key,Value
TestKey,TestValue
"""
        config = ParserConfiguration()
        result = parse(data=data, config=config)

        assert isinstance(result, ParsedRawSheet)
        assert result.sheet_type == ParsedRawType.SECTIONED
        assert len(result.sections) == 1
        assert result.sections[0].name == "header"
