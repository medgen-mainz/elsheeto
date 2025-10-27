"""Unit tests for stage1 parser."""

import itertools
from pathlib import Path
from typing import Any

import pytest
from syrupy.assertion import SnapshotAssertion

from elsheeto.models.common import ParsedSheetType
from elsheeto.models.csv_stage1 import ParsedRawSheet
from elsheeto.parser.common import (
    CaseConsistency,
    ColumnConsistency,
    CsvDelimiter,
    ParserConfiguration,
)
from elsheeto.parser.stage1 import Parser, from_csv


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
        assert result.sheet_type == ParsedSheetType.SECTIONED
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
        assert result.sheet_type == ParsedSheetType.SECTIONED
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
        assert result.sheet_type == ParsedSheetType.SECTIONLESS
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


class TestParseFunction:
    """Test cases for the parse function."""

    def test_parse_function(self):
        """Test the standalone parse function."""
        data = """[Header]
Key,Value
TestKey,TestValue
"""
        config = ParserConfiguration()
        result = from_csv(data=data, config=config)

        assert isinstance(result, ParsedRawSheet)
        assert result.sheet_type == ParsedSheetType.SECTIONED
        assert len(result.sections) == 1
        assert result.sections[0].name == "header"


class TestFromCsvFunctionSmokeTest:

    path_data = Path(__file__).parent.parent / "data"
    csv_files: list[Path] = sorted(path_data.glob("*/*.csv"))

    delimiters = [CsvDelimiter.COMMA, CsvDelimiter.AUTO]

    args = list(itertools.product(csv_files, delimiters))

    @staticmethod
    def idfn(value: Any) -> str:
        """Return a test ID string value."""
        if isinstance(value, Path):
            return "_".join(str(value).rsplit("/")[-2:])
        elif isinstance(value, CsvDelimiter):
            return value.value
        else:
            raise ValueError("Unexpected value type in idfn")

    @pytest.mark.parametrize("path,delim", args, ids=idfn)
    def test_smoke_test(self, path: Path, delim: CsvDelimiter, snapshot_json: SnapshotAssertion):
        """Run smoke test for all CSV files."""
        # arrange

        with path.open("r", encoding="utf-8") as f:
            data = f.read()
        config = ParserConfiguration(delimiter=delim)

        # act

        result = from_csv(data=data, config=config)

        # assert

        snapshot_json.assert_match(result.model_dump(mode="json"))
