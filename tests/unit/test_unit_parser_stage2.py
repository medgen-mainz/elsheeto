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
from elsheeto.parser.common import CsvDelimiter, ParserConfiguration
from elsheeto.parser.stage2 import Parser, from_stage1


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
        assert header.key_values["IEMFileVersion"] == "5"
        assert header.key_values["Experiment Name"] == "MyExperiment"
        assert header.key_values["Date"] == "2023-01-01"

        # Check data section
        data = result.data_section
        assert data.headers == ["Sample_ID", "Sample_Name", "Sample_Plate", "Sample_Well"]
        assert len(data.data) == 2
        assert data.data[0] == ["S1", "Sample1", "Plate1", "A01"]
        assert data.header_to_index["Sample_ID"] == 0

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
        assert data.headers == ["SampleName", "Index1", "Index2", "Lane"]
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
        assert data.headers == ["Sample_ID", "Sample_Name", "Project"]
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
        assert result.header_sections[0].key_values["IEMFileVersion"] == "5"
        assert result.header_sections[1].key_values["Setting1"] == "Value1"

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

    def test_parse_single_section_as_data(self):
        """Test parsing when only one section is present - it becomes data section."""
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

        # Single section becomes data section per new rules
        assert len(result.header_sections) == 0
        assert result.data_section.headers == ["Key1", "Value1"]
        assert result.data_section.data == []

    def test_case_sensitivity_headers(self):
        """Test that headers preserve original case."""
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

        # Stage 2 should preserve original case
        config = ParserConfiguration()
        parser = Parser(config)
        result = parser.parse(raw_sheet=raw_sheet)

        assert "KEY1" in result.header_sections[0].key_values
        assert result.data_section.headers == ["COL1", "COL2"]

    def test_single_value_rows(self):
        """Test handling of single-value rows - single section becomes data section."""
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

        # Single section becomes data section per new rules
        assert len(result.header_sections) == 0
        assert result.data_section.headers == ["150"]
        assert result.data_section.data == [["150"]]

    def test_last_section_is_data(self):
        """Test that only the last section is treated as data section."""
        raw_sheet = ParsedRawSheet(
            delimiter=",",
            sheet_type=ParsedSheetType.SECTIONED,
            sections=[
                ParsedRawSection(
                    name="header",
                    num_columns=2,
                    data=[["Key1", "Value1"]],
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

        # First section becomes header, last section becomes data
        assert len(result.header_sections) == 1
        assert result.header_sections[0].name == "header"
        assert result.data_section.headers == ["Col1", "Col2"]
        assert result.data_section.data == [["Val1", "Val2"]]

    def test_no_sections_creates_empty_data(self):
        """Test that no sections results in empty data section."""
        raw_sheet = ParsedRawSheet(
            delimiter=",",
            sheet_type=ParsedSheetType.SECTIONED,
            sections=[],
        )

        config = ParserConfiguration()
        parser = Parser(config)
        result = parser.parse(raw_sheet=raw_sheet)

        # No sections should create empty data section
        assert len(result.header_sections) == 0
        assert result.data_section.headers == []
        assert result.data_section.data == []

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
        assert result.key_values["Key1"] == "Value1"
        assert result.key_values["Key2"] == "Value2"

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
        assert result.headers == ["Col1", "Col2", "Col3"]
        assert len(result.data) == 2
        assert result.header_to_index["Col1"] == 0
        assert result.header_to_index["Col3"] == 2

        # Empty section
        empty_section = ParsedRawSection(name="empty", num_columns=0, data=[])
        result = parser._convert_to_data_section(empty_section)
        assert result.headers == []
        assert result.data == []

    def test_multiple_sections_first_is_header_last_is_data(self):
        """Test that with multiple sections, first becomes header and last becomes data."""
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
        result = parser.parse(raw_sheet=raw_sheet)

        # First section becomes header, last becomes data
        assert len(result.header_sections) == 1
        assert result.header_sections[0].name == "data"
        # Last section (samples) becomes data section
        assert result.data_section.headers == ["Sample", "Index"]
        assert result.data_section.data == [["S1", "AAA"]]

    def test_multiple_sections_with_flexible_fields(self):
        """Test that multiple sections work with flexible fields - first is header, last is data."""
        raw_sheet = ParsedRawSheet(
            delimiter=",",
            sheet_type=ParsedSheetType.SECTIONED,
            sections=[
                ParsedRawSection(
                    name="header",
                    num_columns=4,
                    data=[
                        ["Key1", "Value1", "ExtraField1", "ExtraField2"],
                    ],
                ),
                ParsedRawSection(
                    name="data",
                    num_columns=2,
                    data=[
                        ["Sample", "Value"],
                        ["S1", "V1"],
                    ],
                ),
            ],
        )

        config = ParserConfiguration()
        parser = Parser(config)
        result = parser.parse(raw_sheet=raw_sheet)

        # First section becomes header
        assert len(result.header_sections) == 1
        header = result.header_sections[0]
        assert len(header.rows) == 1
        assert header.rows[0] == ["Key1", "Value1", "ExtraField1", "ExtraField2"]
        # Last section becomes data
        assert result.data_section.headers == ["Sample", "Value"]
        assert result.data_section.data == [["S1", "V1"]]


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
        result = from_stage1(raw_sheet=raw_sheet, config=config)

        assert isinstance(result, ParsedSheet)
        assert result.sheet_type == ParsedSheetType.SECTIONED
        assert len(result.header_sections) == 1
        assert result.data_section is not None


class TestFromStage1FunctionSmokeTest:

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
        raw_sheet = parser_stage1.from_csv(data=data, config=config)

        # act

        result = from_stage1(raw_sheet=raw_sheet, config=config)

        # assert

        snapshot_json.assert_match(result.model_dump(mode="json"))
