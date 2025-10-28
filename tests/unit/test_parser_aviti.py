"""Unit tests for stage 3 parser for Aviti sample sheets."""

import pytest

from elsheeto.models.aviti import AvitiSheet
from elsheeto.models.common import ParsedSheetType
from elsheeto.models.csv_stage2 import (
    DataSection,
    HeaderRow,
    HeaderSection,
    ParsedSheet,
)
from elsheeto.parser.aviti import Parser
from elsheeto.parser.common import ParserConfiguration


def _create_data_section(headers: list[str] | None = None, data: list[list[str]] | None = None) -> DataSection:
    """Helper to create a valid DataSection."""
    headers = headers or []
    data = data or []
    header_to_index = {header: idx for idx, header in enumerate(headers)}
    return DataSection(headers=headers, header_to_index=header_to_index, data=data)


def _create_parsed_sheet(
    header_sections: list[HeaderSection] | None = None,
    data_section: DataSection | None = None,
    delimiter: str = ",",
    sheet_type: ParsedSheetType = ParsedSheetType.SECTIONED,
) -> ParsedSheet:
    """Helper to create a valid ParsedSheet."""
    header_sections = header_sections or []
    data_section = data_section or _create_data_section()
    return ParsedSheet(
        delimiter=delimiter,
        sheet_type=sheet_type,
        header_sections=header_sections,
        data_section=data_section,
    )


class TestParserInit:
    """Test parser initialization."""

    def test_init_with_config(self):
        """Test parser initialization with configuration."""
        config = ParserConfiguration()
        parser = Parser(config)
        assert parser.config is config


class TestParseRunValues:
    """Test RunValues parsing functionality."""

    def test_parse_run_values_basic(self):
        """Test parsing basic RunValues section."""
        config = ParserConfiguration()
        parser = Parser(config)

        run_values_section = HeaderSection(
            name="runvalues",
            rows=[
                HeaderRow(key="KeyName", value="SomeKey"),
                HeaderRow(key="RunId", value="Run123"),
                HeaderRow(key="Experiment", value="Test_Experiment"),
            ],
        )

        parsed_sheet = _create_parsed_sheet(header_sections=[run_values_section])

        run_values = parser._parse_run_values(parsed_sheet)

        assert run_values is not None
        assert run_values.data == {
            "KeyName": "SomeKey",
            "RunId": "Run123",
            "Experiment": "Test_Experiment",
        }

    def test_parse_run_values_no_section(self):
        """Test parsing when no RunValues section is present."""
        config = ParserConfiguration()
        parser = Parser(config)

        header_section = HeaderSection(name="header", rows=[HeaderRow(key="SomeOtherKey", value="SomeValue")])

        parsed_sheet = _create_parsed_sheet(header_sections=[header_section])

        run_values = parser._parse_run_values(parsed_sheet)

        assert run_values is None


class TestParseSettings:
    """Test Settings parsing functionality."""

    def test_parse_settings_basic(self):
        """Test parsing basic Settings section."""
        config = ParserConfiguration()
        parser = Parser(config)

        settings_section = HeaderSection(
            name="settings",
            rows=[
                HeaderRow(key="R1Adapter", value="CGTGCTGGATTGGCTCACCAGACACCTTCCGACAT"),
                HeaderRow(key="R2Adapter", value="AGTTGACAAGCGGTAGCCTGCACACCTTCCGACAT"),
            ],
        )

        parsed_sheet = _create_parsed_sheet(header_sections=[settings_section])

        settings = parser._parse_settings(parsed_sheet)

        assert settings is not None
        assert settings.data == {
            "R1Adapter": "CGTGCTGGATTGGCTCACCAGACACCTTCCGACAT",
            "R2Adapter": "AGTTGACAAGCGGTAGCCTGCACACCTTCCGACAT",
        }

    def test_parse_settings_no_section(self):
        """Test parsing when no Settings section is present."""
        config = ParserConfiguration()
        parser = Parser(config)

        # Use a section that would be detected as samples-related
        header_section = HeaderSection(
            name="header",
            rows=[
                HeaderRow(key="SampleName", value="Sample1"),
                HeaderRow(key="Index1", value="ATGC"),
            ],
        )

        parsed_sheet = _create_parsed_sheet(header_sections=[header_section])

        settings = parser._parse_settings(parsed_sheet)

        assert settings is None


class TestParseSamples:
    """Test samples parsing functionality."""

    def test_parse_samples_basic(self):
        """Test parsing basic sample data."""
        config = ParserConfiguration()
        parser = Parser(config)

        data_section = _create_data_section(
            headers=["SampleName", "Index1", "Index2", "Lane", "Project"],
            data=[
                ["Sample_1", "CCC", "AAA", "1", "Library_Pool_1"],
                ["Sample_2", "TTT", "GGG", "1", "Library_Pool_1"],
            ],
        )

        parsed_sheet = _create_parsed_sheet(data_section=data_section)

        samples = parser._parse_samples(parsed_sheet)

        assert len(samples) == 2

        sample1 = samples[0]
        assert sample1.sample_name == "Sample_1"
        assert sample1.index1 == "CCC"
        assert sample1.index2 == "AAA"
        assert sample1.lane == "1"
        assert sample1.project == "Library_Pool_1"

        sample2 = samples[1]
        assert sample2.sample_name == "Sample_2"
        assert sample2.index1 == "TTT"
        assert sample2.index2 == "GGG"
        assert sample2.lane == "1"
        assert sample2.project == "Library_Pool_1"

    def test_parse_samples_minimal(self):
        """Test parsing minimal sample data (required fields only)."""
        config = ParserConfiguration()
        parser = Parser(config)

        data_section = _create_data_section(
            headers=["SampleName", "Index1", "Index2"],
            data=[
                ["Sample1", "AGGCAGAA", "TGCTACGA"],
                ["Sample2", "CGTTCTCTTG", "CACCAAGTGG"],
            ],
        )

        parsed_sheet = _create_parsed_sheet(data_section=data_section)

        samples = parser._parse_samples(parsed_sheet)

        assert len(samples) == 2

        sample1 = samples[0]
        assert sample1.sample_name == "Sample1"
        assert sample1.index1 == "AGGCAGAA"
        assert sample1.index2 == "TGCTACGA"
        assert sample1.lane is None
        assert sample1.project is None

    def test_parse_samples_with_extra_metadata(self):
        """Test parsing samples with unknown columns stored as extra metadata."""
        config = ParserConfiguration()
        parser = Parser(config)

        data_section = _create_data_section(
            headers=["SampleName", "Index1", "Index2", "Custom_Metadata"],
            data=[
                ["Sample_1", "CCC", "", "Sample_1_metadata"],
            ],
        )

        parsed_sheet = _create_parsed_sheet(data_section=data_section)

        samples = parser._parse_samples(parsed_sheet)

        assert len(samples) == 1
        sample = samples[0]
        assert sample.sample_name == "Sample_1"
        assert sample.index1 == "CCC"
        assert sample.index2 == ""
        assert sample.extra_metadata == {"Custom_Metadata": "Sample_1_metadata"}

    def test_parse_samples_composite_indices(self):
        """Test parsing samples with composite indices."""
        config = ParserConfiguration()
        parser = Parser(config)

        data_section = _create_data_section(
            headers=["SampleName", "Index1", "Index2"],
            data=[
                ["Sample1", "ATGC+TCGA", "CCGG+TTAA"],
            ],
        )

        parsed_sheet = _create_parsed_sheet(data_section=data_section)

        samples = parser._parse_samples(parsed_sheet)

        assert len(samples) == 1
        sample = samples[0]
        assert sample.sample_name == "Sample1"
        assert sample.index1 == "ATGC+TCGA"
        assert sample.index2 == "CCGG+TTAA"

    def test_parse_samples_empty_values(self):
        """Test parsing samples with empty values."""
        config = ParserConfiguration()
        parser = Parser(config)

        data_section = _create_data_section(
            headers=["SampleName", "Index1", "Index2", "Lane", "Project"],
            data=[
                ["Sample1", "ATGC", "", "", ""],
                ["Sample2", "TCGA", "CCGG", "2", ""],
            ],
        )

        parsed_sheet = _create_parsed_sheet(data_section=data_section)

        samples = parser._parse_samples(parsed_sheet)

        assert len(samples) == 2

        sample1 = samples[0]
        assert sample1.sample_name == "Sample1"
        assert sample1.index1 == "ATGC"
        assert sample1.index2 == ""
        assert sample1.lane is None
        assert sample1.project is None

        sample2 = samples[1]
        assert sample2.sample_name == "Sample2"
        assert sample2.index1 == "TCGA"
        assert sample2.index2 == "CCGG"
        assert sample2.lane == "2"
        assert sample2.project is None

    def test_parse_samples_no_data(self):
        """Test parsing when samples section is empty."""
        config = ParserConfiguration()
        parser = Parser(config)

        data_section = _create_data_section()

        parsed_sheet = _create_parsed_sheet(data_section=data_section)

        samples = parser._parse_samples(parsed_sheet)

        assert samples == []

    def test_parse_samples_missing_sample_name(self):
        """Test parsing fails when required SampleName is missing."""
        config = ParserConfiguration()
        parser = Parser(config)

        data_section = _create_data_section(headers=["Index1", "Index2"], data=[["ATGC", "TCGA"]])

        parsed_sheet = _create_parsed_sheet(data_section=data_section)

        with pytest.raises(ValueError, match="Missing required SampleName"):
            parser._parse_samples(parsed_sheet)

    def test_parse_samples_missing_index1(self):
        """Test parsing fails when required Index1 is missing."""
        config = ParserConfiguration()
        parser = Parser(config)

        data_section = _create_data_section(headers=["SampleName", "Index2"], data=[["Sample1", "TCGA"]])

        parsed_sheet = _create_parsed_sheet(data_section=data_section)

        with pytest.raises(ValueError, match="Missing required Index1"):
            parser._parse_samples(parsed_sheet)

    def test_parse_samples_more_values_than_headers(self):
        """Test parsing samples where a row has more values than headers."""
        config = ParserConfiguration()
        parser = Parser(config)

        data_section = _create_data_section(
            headers=["SampleName", "Index1"],
            data=[
                ["Sample1", "ATGC", "ExtraValue1", "ExtraValue2"],  # More values than headers
            ],
        )

        parsed_sheet = _create_parsed_sheet(data_section=data_section)

        samples = parser._parse_samples(parsed_sheet)

        assert len(samples) == 1
        sample = samples[0]
        assert sample.sample_name == "Sample1"
        assert sample.index1 == "ATGC"
        assert sample.index2 == ""  # Missing Index2 defaults to empty string

    def test_parse_samples_whitespace_normalization(self):
        """Test parsing samples with whitespace-only values that get normalized to None."""
        config = ParserConfiguration()
        parser = Parser(config)

        data_section = _create_data_section(
            headers=["SampleName", "Index1", "Index2", "Lane"],
            data=[
                ["Sample1", "ATGC", "TCGA", "   "],  # Whitespace-only lane
            ],
        )

        parsed_sheet = _create_parsed_sheet(data_section=data_section)

        samples = parser._parse_samples(parsed_sheet)

        assert len(samples) == 1
        sample = samples[0]
        assert sample.sample_name == "Sample1"
        assert sample.index1 == "ATGC"
        assert sample.index2 == "TCGA"
        assert sample.lane is None  # Whitespace-only normalized to None


class TestParseComplete:
    """Test complete parsing functionality."""

    def test_parse_sheet_full(self):
        """Test parsing a complete Aviti sample sheet."""
        config = ParserConfiguration()
        parser = Parser(config)

        settings_section = HeaderSection(
            name="settings",
            rows=[
                HeaderRow(key="R1Adapter", value="CGTGCTGGATTGGCTCACCAGACACCTTCCGACAT"),
                HeaderRow(key="R2Adapter", value="AGTTGACAAGCGGTAGCCTGCACACCTTCCGACAT"),
            ],
        )

        data_section = _create_data_section(
            headers=["SampleName", "Index1", "Index2"],
            data=[
                ["Sample1", "AGGCAGAA", "TGCTACGA"],
                ["Sample2", "CGTTCTCTTG", "CACCAAGTGG"],
            ],
        )

        parsed_sheet = _create_parsed_sheet(header_sections=[settings_section], data_section=data_section)

        aviti_sheet = parser.parse(parsed_sheet=parsed_sheet)

        assert isinstance(aviti_sheet, AvitiSheet)
        assert aviti_sheet.run_values is None
        assert aviti_sheet.settings is not None
        assert aviti_sheet.settings.data["R1Adapter"] == "CGTGCTGGATTGGCTCACCAGACACCTTCCGACAT"
        assert len(aviti_sheet.samples) == 2
        assert aviti_sheet.samples[0].sample_name == "Sample1"
        assert aviti_sheet.samples[1].sample_name == "Sample2"

    def test_parse_minimal_aviti_sheet(self):
        """Test parsing a minimal Aviti sample sheet."""
        config = ParserConfiguration()
        parser = Parser(config)

        data_section = _create_data_section(
            headers=["SampleName", "Index1", "Index2"],
            data=[["Sample1", "ATGC", "TCGA"]],
        )

        parsed_sheet = _create_parsed_sheet(data_section=data_section)

        aviti_sheet = parser.parse(parsed_sheet=parsed_sheet)

        assert isinstance(aviti_sheet, AvitiSheet)
        assert aviti_sheet.run_values is None
        assert aviti_sheet.settings is None
        assert len(aviti_sheet.samples) == 1
        assert aviti_sheet.samples[0].sample_name == "Sample1"


class TestParseFunctionInterface:
    """Test the module-level parse function."""

    def test_parse_function(self):
        """Test the module-level parse function."""
        from elsheeto.parser.aviti import from_stage2

        config = ParserConfiguration()

        data_section = _create_data_section(
            headers=["SampleName", "Index1", "Index2"],
            data=[["Sample1", "ATGC", "TCGA"]],
        )

        parsed_sheet = _create_parsed_sheet(data_section=data_section)

        aviti_sheet = from_stage2(parsed_sheet=parsed_sheet, config=config)

        assert isinstance(aviti_sheet, AvitiSheet)
        assert len(aviti_sheet.samples) == 1
        assert aviti_sheet.samples[0].sample_name == "Sample1"
