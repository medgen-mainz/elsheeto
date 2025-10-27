"""Unit tests for stage2 parser."""

import itertools
from pathlib import Path
from typing import Any

import pytest
from syrupy.assertion import SnapshotAssertion

import elsheeto.parser.stage1 as parser_stage1
from elsheeto.models.common import ParsedSheetType
from elsheeto.models.csv_stage1 import ParsedRawSection, ParsedRawSheet
from elsheeto.models.csv_stage2 import ParsedSheet
from elsheeto.parser.common import CaseConsistency, CsvDelimiter, ParserConfiguration
from elsheeto.parser.stage2 import Parser, parse


class TestParser:
    """Test cases for the stage2 Parser class."""

    def test_init(self):
        """Test Parser initialization."""
        config = ParserConfiguration()
        parser = Parser(config)
        assert parser.config == config

    def test_parse_illumina_style_sectioned(self):
        """Test parsing Illumina-style sectioned data."""
        # Create raw sheet with Header and Data sections
        raw_sheet = ParsedRawSheet(
            delimiter=",",
            sheet_type=ParsedSheetType.SECTIONED,
            sections=[
                ParsedRawSection(
                    name="header",
                    num_columns=2,
                    data=[
                        ["IEMFileVersion", "5"],
                        ["Experiment Name", "MyExperiment"],
                        ["Date", "2023-01-01"],
                    ],
                ),
                ParsedRawSection(
                    name="data",
                    num_columns=4,
                    data=[
                        ["Sample_ID", "Sample_Name", "Sample_Plate", "Sample_Well"],
                        ["S1", "Sample1", "Plate1", "A01"],
                        ["S2", "Sample2", "Plate1", "A02"],
                    ],
                ),
            ],
        )

        config = ParserConfiguration()
        parser = Parser(config)
        result = parser.parse(raw_sheet=raw_sheet)

        assert result.delimiter == ","
        assert result.sheet_type == ParsedSheetType.SECTIONED
        assert len(result.header_sections) == 1
        assert result.data_section is not None

        # Check header section
        header = result.header_sections[0]
        assert header.key_values["iemfileversion"] == "5"
        assert header.key_values["experiment name"] == "MyExperiment"
        assert header.key_values["date"] == "2023-01-01"

        # Check data section
        data = result.data_section
        assert data.headers == ["sample_id", "sample_name", "sample_plate", "sample_well"]
        assert len(data.data) == 2
        assert data.data[0] == ["S1", "Sample1", "Plate1", "A01"]
        assert data.header_to_index["sample_id"] == 0

    def test_parse_aviti_style_sectioned(self):
        """Test parsing Aviti-style sectioned data."""
        raw_sheet = ParsedRawSheet(
            delimiter=",",
            sheet_type=ParsedSheetType.SECTIONED,
            sections=[
                ParsedRawSection(
                    name="samples",
                    num_columns=4,
                    data=[
                        ["SampleName", "Index1", "Index2", "Lane"],
                        ["Sample_1", "CCC", "AAA", "1"],
                        ["Sample_2", "TTT", "GGG", "1"],
                    ],
                ),
            ],
        )

        config = ParserConfiguration()
        parser = Parser(config)
        result = parser.parse(raw_sheet=raw_sheet)

        assert result.sheet_type == ParsedSheetType.SECTIONED
        assert len(result.header_sections) == 0  # No header sections
        assert result.data_section is not None

        # Check data section
        data = result.data_section
        assert data.headers == ["samplename", "index1", "index2", "lane"]
        assert len(data.data) == 2
        assert data.data[0] == ["Sample_1", "CCC", "AAA", "1"]

    def test_parse_sectionless(self):
        """Test parsing sectionless CSV data."""
        raw_sheet = ParsedRawSheet(
            delimiter=",",
            sheet_type=ParsedSheetType.SECTIONLESS,
            sections=[
                ParsedRawSection(
                    name="",
                    num_columns=3,
                    data=[
                        ["Sample_ID", "Sample_Name", "Project"],
                        ["S1", "Sample1", "Proj1"],
                        ["S2", "Sample2", "Proj1"],
                    ],
                ),
            ],
        )

        config = ParserConfiguration()
        parser = Parser(config)
        result = parser.parse(raw_sheet=raw_sheet)

        assert result.sheet_type == ParsedSheetType.SECTIONLESS
        assert len(result.header_sections) == 0
        assert result.data_section is not None

        # Check data section
        data = result.data_section
        assert data.headers == ["sample_id", "sample_name", "project"]
        assert len(data.data) == 2

    def test_parse_multiple_header_sections(self):
        """Test parsing with multiple header sections."""
        raw_sheet = ParsedRawSheet(
            delimiter=",",
            sheet_type=ParsedSheetType.SECTIONED,
            sections=[
                ParsedRawSection(
                    name="header",
                    num_columns=2,
                    data=[["IEMFileVersion", "5"], ["Experiment_Name", "MyExperiment"]],
                ),
                ParsedRawSection(
                    name="settings",
                    num_columns=2,
                    data=[["Setting1", "Value1"], ["Setting2", "Value2"]],
                ),
                ParsedRawSection(
                    name="data",
                    num_columns=2,
                    data=[["Col1", "Col2"], ["Val1", "Val2"]],
                ),
            ],
        )

        config = ParserConfiguration()
        parser = Parser(config)
        result = parser.parse(raw_sheet=raw_sheet)

        assert len(result.header_sections) == 2
        assert result.header_sections[0].key_values["iemfileversion"] == "5"
        assert result.header_sections[1].key_values["setting1"] == "Value1"

    def test_parse_empty_sections(self):
        """Test parsing with empty sections."""
        raw_sheet = ParsedRawSheet(
            delimiter=",",
            sheet_type=ParsedSheetType.SECTIONED,
            sections=[
                ParsedRawSection(name="empty", num_columns=0, data=[]),
                ParsedRawSection(
                    name="data",
                    num_columns=2,
                    data=[["Col1", "Col2"], ["Val1", "Val2"]],
                ),
            ],
        )

        config = ParserConfiguration()
        parser = Parser(config)
        result = parser.parse(raw_sheet=raw_sheet)

        # Empty sections should not create header sections
        assert len(result.header_sections) == 0
        assert result.data_section is not None

    def test_parse_no_data_section(self):
        """Test parsing when no data section is present."""
        raw_sheet = ParsedRawSheet(
            delimiter=",",
            sheet_type=ParsedSheetType.SECTIONED,
            sections=[
                ParsedRawSection(
                    name="header",
                    num_columns=2,
                    data=[["Key1", "Value1"]],
                ),
            ],
        )

        config = ParserConfiguration()
        parser = Parser(config)
        result = parser.parse(raw_sheet=raw_sheet)

        assert len(result.header_sections) == 1
        # Should create empty data section
        assert result.data_section is not None
        assert result.data_section.headers == []
        assert result.data_section.data == []

    def test_case_sensitivity_headers(self):
        """Test case sensitivity for headers."""
        raw_sheet = ParsedRawSheet(
            delimiter=",",
            sheet_type=ParsedSheetType.SECTIONED,
            sections=[
                ParsedRawSection(
                    name="header",
                    num_columns=2,
                    data=[["KEY1", "Value1"]],
                ),
                ParsedRawSection(
                    name="data",
                    num_columns=2,
                    data=[["COL1", "COL2"], ["Val1", "Val2"]],
                ),
            ],
        )

        # Case insensitive (default)
        config = ParserConfiguration()
        parser = Parser(config)
        result = parser.parse(raw_sheet=raw_sheet)

        assert "key1" in result.header_sections[0].key_values
        assert result.data_section.headers == ["col1", "col2"]

        # Case sensitive
        config = ParserConfiguration(
            key_case=CaseConsistency.CASE_SENSITIVE,
            column_header_case=CaseConsistency.CASE_SENSITIVE,
        )
        parser = Parser(config)
        result = parser.parse(raw_sheet=raw_sheet)

        assert "KEY1" in result.header_sections[0].key_values
        assert result.data_section.headers == ["COL1", "COL2"]

    def test_single_value_rows(self):
        """Test handling of single-value rows (e.g., Reads section)."""
        raw_sheet = ParsedRawSheet(
            delimiter=",",
            sheet_type=ParsedSheetType.SECTIONED,
            sections=[
                ParsedRawSection(
                    name="reads",
                    num_columns=1,
                    data=[["150"], ["150"]],
                ),
            ],
        )

        config = ParserConfiguration()
        parser = Parser(config)
        result = parser.parse(raw_sheet=raw_sheet)

        assert len(result.header_sections) == 1
        header = result.header_sections[0]
        assert header.key_values["value_0"] == "150"
        assert header.key_values["value_1"] == "150"

    def test_is_data_section(self):
        """Test data section identification."""
        config = ParserConfiguration()
        parser = Parser(config)

        # Known data section names
        data_section = ParsedRawSection(name="data", num_columns=2, data=[])
        assert parser._is_data_section(data_section)

        samples_section = ParsedRawSection(name="samples", num_columns=2, data=[])
        assert parser._is_data_section(samples_section)

        # Section with tabular structure
        tabular_section = ParsedRawSection(
            name="custom",
            num_columns=2,
            data=[["Header1", "Header2"], ["Val1", "Val2"]],
        )
        assert parser._is_data_section(tabular_section)

        # Key-value section
        header_section = ParsedRawSection(
            name="header",
            num_columns=2,
            data=[["Key", "Value"]],
        )
        assert not parser._is_data_section(header_section)

    def test_has_tabular_structure(self):
        """Test tabular structure detection."""
        config = ParserConfiguration()
        parser = Parser(config)

        # Valid tabular structure
        tabular_section = ParsedRawSection(
            name="test",
            num_columns=3,
            data=[
                ["Header1", "Header2", "Header3"],
                ["Val1", "Val2", "Val3"],
                ["Val4", "Val5", "Val6"],
            ],
        )
        assert parser._has_tabular_structure(tabular_section)

        # Too few rows
        short_section = ParsedRawSection(name="test", num_columns=2, data=[["Header1", "Header2"]])
        assert not parser._has_tabular_structure(short_section)

        # Empty headers
        empty_header_section = ParsedRawSection(name="test", num_columns=2, data=[["", ""], ["Val1", "Val2"]])
        assert not parser._has_tabular_structure(empty_header_section)

        # Inconsistent column counts
        inconsistent_section = ParsedRawSection(
            name="test",
            num_columns=3,
            data=[["H1", "H2"], ["V1", "V2", "V3", "V4"]],  # Very different column counts
        )
        assert not parser._has_tabular_structure(inconsistent_section)

    def test_convert_to_header_section(self):
        """Test header section conversion."""
        config = ParserConfiguration()
        parser = Parser(config)

        # Normal key-value pairs
        section = ParsedRawSection(
            name="header",
            num_columns=2,
            data=[
                ["Key1", "Value1"],
                ["Key2", "Value2"],
                ["", ""],  # Empty row should be skipped
            ],
        )
        result = parser._convert_to_header_section(section)
        assert result is not None
        assert result.key_values["key1"] == "Value1"
        assert result.key_values["key2"] == "Value2"

        # Empty section
        empty_section = ParsedRawSection(name="empty", num_columns=0, data=[])
        result = parser._convert_to_header_section(empty_section)
        assert result is None

    def test_convert_to_data_section(self):
        """Test data section conversion."""
        config = ParserConfiguration()
        parser = Parser(config)

        # Normal tabular data
        section = ParsedRawSection(
            name="data",
            num_columns=3,
            data=[
                ["Col1", "Col2", "Col3"],
                ["Val1", "Val2", "Val3"],
                ["Val4", "Val5", "Val6"],
            ],
        )
        result = parser._convert_to_data_section(section)
        assert result.headers == ["col1", "col2", "col3"]
        assert len(result.data) == 2
        assert result.header_to_index["col1"] == 0
        assert result.header_to_index["col3"] == 2

        # Empty section
        empty_section = ParsedRawSection(name="empty", num_columns=0, data=[])
        result = parser._convert_to_data_section(empty_section)
        assert result.headers == []
        assert result.data == []

    def test_multiple_data_sections_warning(self, caplog):
        """Test warning when multiple data sections are found."""
        raw_sheet = ParsedRawSheet(
            delimiter=",",
            sheet_type=ParsedSheetType.SECTIONED,
            sections=[
                ParsedRawSection(
                    name="data",
                    num_columns=2,
                    data=[["Col1", "Col2"], ["Val1", "Val2"]],
                ),
                ParsedRawSection(
                    name="samples",
                    num_columns=2,
                    data=[["Sample", "Index"], ["S1", "AAA"]],
                ),
            ],
        )

        config = ParserConfiguration()
        parser = Parser(config)

        with caplog.at_level("WARNING"):
            result = parser.parse(raw_sheet=raw_sheet)

        # Should warn about multiple data sections
        assert "Multiple data sections found" in caplog.text
        # Should use the last data section (samples)
        assert result.data_section.headers == ["sample", "index"]


class TestParseFunction:
    """Test cases for the parse function."""

    def test_parse_function(self):
        """Test the standalone parse function."""
        raw_sheet = ParsedRawSheet(
            delimiter=",",
            sheet_type=ParsedSheetType.SECTIONED,
            sections=[
                ParsedRawSection(
                    name="header",
                    num_columns=2,
                    data=[["Key", "Value"]],
                ),
                ParsedRawSection(
                    name="data",
                    num_columns=2,
                    data=[["Col1", "Col2"], ["Val1", "Val2"]],
                ),
            ],
        )

        config = ParserConfiguration()
        result = parse(raw_sheet=raw_sheet, config=config)

        assert isinstance(result, ParsedSheet)
        assert result.sheet_type == ParsedSheetType.SECTIONED
        assert len(result.header_sections) == 1
        assert result.data_section is not None


class TestParseFunctionSmokeTest:

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
        raw_sheet = parser_stage1.parse(data=data, config=config)

        # act

        result = parse(raw_sheet=raw_sheet, config=config)

        # assert

        snapshot_json.assert_match(result.model_dump(mode="json"))
