"""Unit tests for stage1 parser."""

import itertools
import warnings
from pathlib import Path
from typing import Any

import pytest
from syrupy.assertion import SnapshotAssertion

from elsheeto.exceptions import ColumnConsistencyWarning
from elsheeto.models.common import ParsedSheetType
from elsheeto.models.csv_stage1 import ParsedRawSheet
from elsheeto.parser.common import (
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
        assert header_section.name == "Header"
        assert header_section.num_columns == 5
        assert len(header_section.data) == 2  # Two non-empty rows
        assert header_section.data[0] == ["IEMFileVersion", "5", "", "", ""]

        # Check Data section
        data_section = result.sections[1]
        assert data_section.name == "Data"
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
        assert samples_section.name == "Samples"
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
        assert header_section.name == "Header"
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
        assert header_section.name == "Header"
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
        """Test that section headers preserve original case."""
        data = """[HEADER]
Key,Value
TestKey,TestValue
"""
        # Stage 1 should preserve original case
        config = ParserConfiguration()
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

        with pytest.raises(ValueError, match="Section 'Section1' column consistency violated"):
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

    def test_column_consistency_warn_and_pad(self):
        """Test warn and pad column consistency mode."""
        data = """[Section1]
A,B,C
1,2,3
4,5
"""
        config = ParserConfiguration(column_consistency=ColumnConsistency.WARN_AND_PAD)
        parser = Parser(config)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = parser.parse(data=data)

            # Should parse without exceptions
            assert len(result.sections) == 1
            section = result.sections[0]
            assert section.num_columns == 3

            # Check that data was padded
            assert len(section.data) == 3
            assert section.data[0] == ["A", "B", "C"]
            assert section.data[1] == ["1", "2", "3"]
            assert section.data[2] == ["4", "5", ""]  # Padded with empty string

            # Should have issued a warning
            assert len(w) == 1
            assert issubclass(w[0].category, ColumnConsistencyWarning)
            assert "padding missing cells" in str(w[0].message)

    def test_column_consistency_warn_and_pad_github_issue_example(self):
        """Test warn and pad with the GitHub issue example."""
        data = """[SAMPLES]
SampleName,Index1,Index2,Project
PhiX,ATGTCGCTAG,CTAGCTCGTA
PhiX,CACAGATCGT,ACGAGAGTCT
PhiX,GCACATAGTC,GACTACTAGC
PhiX,TGTGTCGACA,TGTCTGACAG
"""
        config = ParserConfiguration(column_consistency=ColumnConsistency.WARN_AND_PAD)
        parser = Parser(config)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = parser.parse(data=data)

            # Should parse without exceptions
            assert len(result.sections) == 1
            section = result.sections[0]
            assert section.name == "SAMPLES"
            assert section.num_columns == 4

            # Check that data was padded correctly
            assert len(section.data) == 5
            assert section.data[0] == ["SampleName", "Index1", "Index2", "Project"]
            # All sample rows should be padded with empty Project column
            for i in range(1, 5):
                assert len(section.data[i]) == 4
                assert section.data[i][3] == ""  # Empty Project column

            # Should have issued a warning
            assert len(w) == 1
            assert issubclass(w[0].category, ColumnConsistencyWarning)
            assert "padding missing cells" in str(w[0].message)

    def test_column_consistency_default_is_warn_and_pad(self):
        """Test that the default configuration uses WARN_AND_PAD."""
        config = ParserConfiguration()
        assert config.column_consistency == ColumnConsistency.WARN_AND_PAD

    def test_column_consistency_warn_and_pad_no_warning_if_consistent(self):
        """Test that WARN_AND_PAD doesn't issue warnings for consistent columns."""
        data = """[Section1]
A,B,C
1,2,3
4,5,6
"""
        config = ParserConfiguration(column_consistency=ColumnConsistency.WARN_AND_PAD)
        parser = Parser(config)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = parser.parse(data=data)

            # Should parse without exceptions or warnings
            assert len(result.sections) == 1
            assert result.sections[0].num_columns == 3
            assert len(w) == 0  # No warnings should be issued

    def test_column_consistency_pad(self):
        """Test PAD column consistency mode (silent padding)."""
        data = """[Section1]
A,B,C
1,2,3
4,5
"""
        config = ParserConfiguration(column_consistency=ColumnConsistency.PAD)
        parser = Parser(config)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = parser.parse(data=data)

            # Should parse without exceptions
            assert len(result.sections) == 1
            section = result.sections[0]
            assert section.num_columns == 3

            # Check that data was padded
            assert len(section.data) == 3
            assert section.data[0] == ["A", "B", "C"]
            assert section.data[1] == ["1", "2", "3"]
            assert section.data[2] == ["4", "5", ""]  # Padded with empty string

            # Should NOT have issued any warnings
            assert len(w) == 0  # No warnings for PAD mode

    def test_column_consistency_pad_github_issue_example(self):
        """Test PAD mode with the GitHub issue example."""
        data = """[SAMPLES]
SampleName,Index1,Index2,Project
PhiX,ATGTCGCTAG,CTAGCTCGTA
PhiX,CACAGATCGT,ACGAGAGTCT
PhiX,GCACATAGTC,GACTACTAGC
PhiX,TGTGTCGACA,TGTCTGACAG
"""
        config = ParserConfiguration(column_consistency=ColumnConsistency.PAD)
        parser = Parser(config)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = parser.parse(data=data)

            # Should parse without exceptions
            assert len(result.sections) == 1
            section = result.sections[0]
            assert section.name == "SAMPLES"
            assert section.num_columns == 4

            # Check that data was padded correctly
            assert len(section.data) == 5
            assert section.data[0] == ["SampleName", "Index1", "Index2", "Project"]
            # All sample rows should be padded with empty Project column
            for i in range(1, 5):
                assert len(section.data[i]) == 4
                assert section.data[i][3] == ""  # Empty Project column

            # Should NOT have issued any warnings
            assert len(w) == 0  # No warnings for PAD mode

    def test_column_consistency_pad_vs_warn_and_pad_comparison(self):
        """Test that PAD and WARN_AND_PAD produce same results but different warnings."""
        data = """[Section1]
A,B,C
1,2
"""

        # Test PAD mode
        config_pad = ParserConfiguration(column_consistency=ColumnConsistency.PAD)
        parser_pad = Parser(config_pad)

        with warnings.catch_warnings(record=True) as w_pad:
            warnings.simplefilter("always")
            result_pad = parser_pad.parse(data=data)

        # Test WARN_AND_PAD mode
        config_warn = ParserConfiguration(column_consistency=ColumnConsistency.WARN_AND_PAD)
        parser_warn = Parser(config_warn)

        with warnings.catch_warnings(record=True) as w_warn:
            warnings.simplefilter("always")
            result_warn = parser_warn.parse(data=data)

        # Both should produce the same padded results
        assert len(result_pad.sections) == len(result_warn.sections) == 1
        pad_section = result_pad.sections[0]
        warn_section = result_warn.sections[0]

        assert pad_section.num_columns == warn_section.num_columns == 3
        assert pad_section.data == warn_section.data == [["A", "B", "C"], ["1", "2", ""]]

        # But different warning behavior
        assert len(w_pad) == 0  # PAD mode: no warnings
        assert len(w_warn) == 1  # WARN_AND_PAD mode: warning issued
        assert issubclass(w_warn[0].category, ColumnConsistencyWarning)

    def test_column_consistency_edge_cases(self):
        """Test edge cases to improve code coverage."""
        config = ParserConfiguration()
        Parser(config)

        # Test STRICT_GLOBAL with empty sections list (line 270)
        config_global = ParserConfiguration(column_consistency=ColumnConsistency.STRICT_GLOBAL)
        parser_global = Parser(config_global)

        # Empty data should not cause issues
        data_empty = ""
        result = parser_global.parse(data=data_empty)
        assert len(result.sections) == 1  # Creates an empty section
        assert result.sections[0].num_columns == 0

        # Test sections with no data (lines 329, 338, 376)
        data_no_content = """[EmptySection]
"""

        # Test PAD mode with empty section
        config_pad = ParserConfiguration(column_consistency=ColumnConsistency.PAD)
        parser_pad = Parser(config_pad)
        result_pad = parser_pad.parse(data=data_no_content)
        assert len(result_pad.sections) == 1
        assert result_pad.sections[0].data == []

        # Test WARN_AND_PAD mode with empty section
        config_warn = ParserConfiguration(column_consistency=ColumnConsistency.WARN_AND_PAD)
        parser_warn = Parser(config_warn)
        result_warn = parser_warn.parse(data=data_no_content)
        assert len(result_warn.sections) == 1
        assert result_warn.sections[0].data == []

        # Test sections with only empty rows (lines 338, 376)
        data_empty_rows = """[SectionWithEmptyRows]


"""

        result_pad_empty = parser_pad.parse(data=data_empty_rows)
        assert len(result_pad_empty.sections) == 1
        # Empty rows should be preserved but section should indicate no real columns

        result_warn_empty = parser_warn.parse(data=data_empty_rows)
        assert len(result_warn_empty.sections) == 1

    def test_strict_sectioned_with_empty_rows(self):
        """Test STRICT_SECTIONED mode with empty rows to cover line 312."""
        data = """[Section1]
A,B,C


1,2,3
"""
        config = ParserConfiguration(column_consistency=ColumnConsistency.STRICT_SECTIONED)
        parser = Parser(config)

        # Should parse successfully, skipping empty rows
        result = parser.parse(data=data)
        assert len(result.sections) == 1
        assert result.sections[0].num_columns == 3

    def test_pad_section_with_empty_rows(self):
        """Test padding with empty rows to cover lines 345-346."""
        data = """[Section1]
A,B,C

1,2

"""
        # Disable ignore_empty_lines to preserve empty rows
        config = ParserConfiguration(column_consistency=ColumnConsistency.PAD, ignore_empty_lines=False)
        parser = Parser(config)

        result = parser.parse(data=data)
        assert len(result.sections) == 1
        section = result.sections[0]
        assert section.num_columns == 3

        # Check that empty rows are preserved and non-empty rows are padded
        assert len(section.data) == 4  # Header, empty line, data row, empty line
        assert section.data[0] == ["A", "B", "C"]
        assert section.data[1] == []  # Empty row preserved as empty list
        assert section.data[2] == ["1", "2", ""]  # Padded
        assert section.data[3] == []  # Empty row preserved as empty list

    def test_section_with_only_empty_rows(self):
        """Test sections with only empty rows to cover lines 338, 376."""
        # Create data with completely empty lines (no spaces)
        data_only_empty = "[OnlyEmpty]\n\n\n"

        # Test PAD mode with only empty rows (line 338)
        config_pad = ParserConfiguration(column_consistency=ColumnConsistency.PAD, ignore_empty_lines=False)
        parser_pad = Parser(config_pad)
        result_pad = parser_pad.parse(data=data_only_empty)

        # Should handle gracefully
        assert len(result_pad.sections) == 1
        section_pad = result_pad.sections[0]
        # Section should have 0 columns since all rows are empty
        assert section_pad.num_columns == 0

        # Test WARN_AND_PAD mode with only empty rows (line 376)
        config_warn = ParserConfiguration(column_consistency=ColumnConsistency.WARN_AND_PAD, ignore_empty_lines=False)
        parser_warn = Parser(config_warn)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result_warn = parser_warn.parse(data=data_only_empty)

            # Should handle gracefully and not issue warnings
            assert len(result_warn.sections) == 1
            assert result_warn.sections[0].num_columns == 0
            assert len(w) == 0  # No warnings for empty sections

    def test_strict_validation_skip_empty_row(self):
        """Test strict validation skipping empty rows to cover line 312."""
        data = """[StrictSection]
A,B,C

1,2,3
"""
        config = ParserConfiguration(
            column_consistency=ColumnConsistency.STRICT_SECTIONED,
            ignore_empty_lines=False,  # Keep empty lines to test the skip logic
        )
        parser = Parser(config)

        # Should succeed by skipping the empty row
        result = parser.parse(data=data)
        assert len(result.sections) == 1
        assert result.sections[0].num_columns == 3

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

        assert parser._extract_section_name(["[Header]"]) == "Header"
        assert parser._extract_section_name(["  [Data]  "]) == "Data"
        assert parser._extract_section_name(["[Settings]", "extra", "columns"]) == "Settings"
        assert parser._extract_section_name(["not a section"]) is None
        assert parser._extract_section_name(["[incomplete"]) is None
        assert parser._extract_section_name([""]) is None

    def test_extract_section_name_preserves_case(self):
        """Test section name extraction preserves original case."""
        config = ParserConfiguration()
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
        assert result.sections[0].name == "Header"


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
