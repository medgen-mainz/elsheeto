"""Unit tests for stage 3 parser for Illumina v1 sample sheets."""

import pytest

from elsheeto.models.common import ParsedSheetType
from elsheeto.models.csv_stage2 import (
    DataSection,
    HeaderRow,
    HeaderSection,
    ParsedSheet,
)
from elsheeto.models.illumina_v1 import (
    IlluminaSampleSheet,
)
from elsheeto.parser.common import ParserConfiguration
from elsheeto.parser.illumina_v1 import Parser


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


class TestParseHeader:
    """Test header parsing functionality."""

    def test_parse_header_basic(self):
        """Test parsing basic header information."""
        config = ParserConfiguration()
        parser = Parser(config)

        header_section = HeaderSection(
            name="header",
            rows=[
                HeaderRow(key="IEMFileVersion", value="4"),
                HeaderRow(key="Investigator Name", value="John Doe"),
                HeaderRow(key="Experiment Name", value="Test Experiment"),
                HeaderRow(key="Date", value="2023-01-01"),
                HeaderRow(key="Workflow", value="GenerateFASTQ"),
                HeaderRow(key="Application", value="FASTQ Only"),
                HeaderRow(key="Instrument Type", value="MiSeq"),
                HeaderRow(key="Assay", value="TruSeq HT"),
                HeaderRow(key="Index Adapters", value="TruSeq HT"),
                HeaderRow(key="Description", value="Test description"),
                HeaderRow(key="Chemistry", value="Amplicon"),
            ],
        )

        parsed_sheet = _create_parsed_sheet(header_sections=[header_section])

        header = parser._parse_header(parsed_sheet)

        assert header.iem_file_version == "4"
        assert header.investigator_name == "John Doe"
        assert header.experiment_name == "Test Experiment"
        assert header.date == "2023-01-01"
        assert header.workflow == "GenerateFASTQ"
        assert header.application == "FASTQ Only"
        assert header.instrument_type == "MiSeq"
        assert header.assay == "TruSeq HT"
        assert header.index_adapters == "TruSeq HT"
        assert header.description == "Test description"
        assert header.chemistry == "Amplicon"

    def test_parse_header_case_insensitive(self):
        """Test that header parsing is case-insensitive."""
        config = ParserConfiguration()
        parser = Parser(config)

        header_section = HeaderSection(
            name="header",
            rows=[
                HeaderRow(key="iemfileversion", value="4"),
                HeaderRow(key="INVESTIGATOR NAME", value="Jane Smith"),
                HeaderRow(key="experiment name", value="Mixed Case Test"),
            ],
        )

        parsed_sheet = _create_parsed_sheet(header_sections=[header_section])

        header = parser._parse_header(parsed_sheet)

        assert header.iem_file_version == "4"
        assert header.investigator_name == "Jane Smith"
        assert header.experiment_name == "Mixed Case Test"

    def test_parse_header_with_extra_metadata(self):
        """Test parsing header with unknown fields stored as extra metadata."""
        config = ParserConfiguration()
        parser = Parser(config)

        header_section = HeaderSection(
            name="header",
            rows=[
                HeaderRow(key="IEMFileVersion", value="4"),
                HeaderRow(key="Investigator Name", value="John Doe"),
                HeaderRow(key="Custom Field", value="Custom Value"),
                HeaderRow(key="Another Field", value="Another Value"),
            ],
        )

        parsed_sheet = _create_parsed_sheet(header_sections=[header_section])

        header = parser._parse_header(parsed_sheet)

        assert header.iem_file_version == "4"
        assert header.investigator_name == "John Doe"
        assert header.extra_metadata == {
            "Custom Field": "Custom Value",
            "Another Field": "Another Value",
        }

    def test_parse_header_multiple_sections(self):
        """Test parsing header from multiple header sections."""
        config = ParserConfiguration()
        parser = Parser(config)

        header_sections = [
            HeaderSection(
                name="header",
                rows=[
                    HeaderRow(key="IEMFileVersion", value="4"),
                    HeaderRow(key="Investigator Name", value="John Doe"),
                    HeaderRow(key="Experiment Name", value="Test Experiment"),
                    HeaderRow(key="Date", value="2023-01-01"),
                ],
            ),
        ]

        parsed_sheet = _create_parsed_sheet(header_sections=header_sections)

        header = parser._parse_header(parsed_sheet)

        assert header.iem_file_version == "4"
        assert header.investigator_name == "John Doe"
        assert header.experiment_name == "Test Experiment"
        assert header.date == "2023-01-01"

    def test_parse_header_no_header_section(self):
        """Test parsing when no header section is present."""
        config = ParserConfiguration()
        parser = Parser(config)

        # Create parsed sheet without any header section
        parsed_sheet = _create_parsed_sheet(header_sections=[])

        header = parser._parse_header(parsed_sheet)

        # Should create minimal header with defaults
        assert header.iem_file_version is None
        assert header.investigator_name is None
        assert header.experiment_name is None
        assert header.date is None
        assert header.workflow == "GenerateFASTQ"
        assert header.application is None
        assert header.instrument_type is None
        assert header.assay is None
        assert header.index_adapters is None
        assert header.description is None
        assert header.chemistry is None
        assert header.run is None
        assert header.extra_metadata == {}


class TestParseReads:
    """Test reads parsing functionality."""

    def test_parse_reads_single_read(self):
        """Test parsing single read length."""
        config = ParserConfiguration()
        parser = Parser(config)

        reads_section = HeaderSection(name="reads", rows=[HeaderRow(key="151", value="")])

        parsed_sheet = _create_parsed_sheet(header_sections=[reads_section])

        reads = parser._parse_reads(parsed_sheet)

        assert reads is not None
        assert reads.read_lengths == [151]

    def test_parse_reads_paired_end(self):
        """Test parsing paired-end read lengths."""
        config = ParserConfiguration()
        parser = Parser(config)

        reads_section = HeaderSection(
            name="reads", rows=[HeaderRow(key="151", value=""), HeaderRow(key="151", value="")]
        )

        parsed_sheet = _create_parsed_sheet(header_sections=[reads_section])

        reads = parser._parse_reads(parsed_sheet)

        assert reads is not None
        assert reads.read_lengths == [151, 151]

    def test_parse_reads_no_reads_section(self):
        """Test parsing when no reads section is present."""
        config = ParserConfiguration()
        parser = Parser(config)

        header_section = HeaderSection(
            name="header",
            rows=[
                HeaderRow(key="IEMFileVersion", value="4"),
                HeaderRow(key="Investigator Name", value="John Doe"),
            ],
        )

        parsed_sheet = _create_parsed_sheet(header_sections=[header_section])

        reads = parser._parse_reads(parsed_sheet)

        assert reads is None

    def test_parse_reads_invalid_row_format(self):
        """Test parsing reads section with invalid row format (non-empty key and value)."""
        config = ParserConfiguration()
        parser = Parser(config)

        reads_section = HeaderSection(
            name="reads",
            rows=[
                HeaderRow(key="151", value=""),  # Valid row
                HeaderRow(key="SomeKey", value="SomeValue"),  # Invalid row (not empty, not key-only)
            ],
        )

        parsed_sheet = _create_parsed_sheet(header_sections=[reads_section])

        reads = parser._parse_reads(parsed_sheet)

        # Should return None due to invalid row format
        assert reads is None

    def test_parse_reads_invalid_numeric_value(self):
        """Test parsing reads section with non-numeric value."""
        config = ParserConfiguration()
        parser = Parser(config)

        reads_section = HeaderSection(
            name="reads",
            rows=[
                HeaderRow(key="abc", value=""),  # Invalid non-numeric key
            ],
        )

        parsed_sheet = _create_parsed_sheet(header_sections=[reads_section])

        reads = parser._parse_reads(parsed_sheet)

        # Should return None due to non-numeric value
        assert reads is None

    def test_parse_reads_empty_reads_section(self):
        """Test parsing empty reads section (no rows)."""
        config = ParserConfiguration()
        parser = Parser(config)

        reads_section = HeaderSection(name="reads", rows=[])

        parsed_sheet = _create_parsed_sheet(header_sections=[reads_section])

        reads = parser._parse_reads(parsed_sheet)

        # Should return None for empty reads section
        assert reads is None


class TestParseSettings:
    """Test settings parsing functionality."""

    def test_parse_settings_basic(self):
        """Test parsing basic settings."""
        config = ParserConfiguration()
        parser = Parser(config)

        settings_section = HeaderSection(
            name="settings",
            rows=[
                HeaderRow(key="SettingOption1", value="Value1"),
                HeaderRow(key="ConfigParameter", value="Value2"),
            ],
        )

        parsed_sheet = _create_parsed_sheet(header_sections=[settings_section])

        settings = parser._parse_settings(parsed_sheet)

        # Settings section is ignored per requirements
        assert settings is None

    def test_parse_settings_no_settings_section(self):
        """Test parsing when no settings section is present."""
        config = ParserConfiguration()
        parser = Parser(config)

        header_section = HeaderSection(
            name="header",
            rows=[
                HeaderRow(key="IEMFileVersion", value="4"),
                HeaderRow(key="Investigator Name", value="John Doe"),
            ],
        )

        parsed_sheet = _create_parsed_sheet(header_sections=[header_section])

        settings = parser._parse_settings(parsed_sheet)

        assert settings is None


class TestParseData:
    """Test data parsing functionality."""

    def test_parse_data_basic(self):
        """Test parsing basic sample data."""
        config = ParserConfiguration()
        parser = Parser(config)

        data_section = _create_data_section(
            headers=["Lane", "Sample_ID", "Sample_Name", "Sample_Project"],
            data=[
                ["1", "Sample1", "Sample One", "Project1"],
                ["2", "Sample2", "Sample Two", "Project2"],
            ],
        )

        parsed_sheet = _create_parsed_sheet(data_section=data_section)

        samples = parser._parse_data(parsed_sheet)

        assert len(samples) == 2

        sample1 = samples[0]
        assert sample1.lane == 1
        assert sample1.sample_id == "Sample1"
        assert sample1.sample_name == "Sample One"
        assert sample1.sample_project == "Project1"

        sample2 = samples[1]
        assert sample2.lane == 2
        assert sample2.sample_id == "Sample2"
        assert sample2.sample_name == "Sample Two"
        assert sample2.sample_project == "Project2"

    def test_parse_data_with_indices(self):
        """Test parsing sample data with index information."""
        config = ParserConfiguration()
        parser = Parser(config)

        data_section = _create_data_section(
            headers=["Sample_ID", "Sample_Name", "I7_Index_ID", "index", "I5_Index_ID", "index2"],
            data=[
                ["Sample1", "Sample One", "N701", "TAAGGCGA", "S501", "TAGATCGC"],
                ["Sample2", "Sample Two", "N702", "CGTACTAG", "S502", "CTCTCTAT"],
            ],
        )

        parsed_sheet = _create_parsed_sheet(data_section=data_section)

        samples = parser._parse_data(parsed_sheet)

        assert len(samples) == 2

        sample1 = samples[0]
        assert sample1.sample_id == "Sample1"
        assert sample1.i7_index_id == "N701"
        assert sample1.index == "TAAGGCGA"
        assert sample1.i5_index_id == "S501"
        assert sample1.index2 == "TAGATCGC"

    def test_parse_data_with_extra_metadata(self):
        """Test parsing data with unknown columns stored as extra metadata."""
        config = ParserConfiguration()
        parser = Parser(config)

        data_section = _create_data_section(
            headers=["Sample_ID", "Sample_Name", "Custom_Field", "Another_Field"],
            data=[
                ["Sample1", "Sample One", "Custom Value", "Another Value"],
            ],
        )

        parsed_sheet = _create_parsed_sheet(data_section=data_section)

        samples = parser._parse_data(parsed_sheet)

        assert len(samples) == 1
        sample = samples[0]
        assert sample.sample_id == "Sample1"
        assert sample.sample_name == "Sample One"
        assert sample.extra_metadata == {
            "Custom_Field": "Custom Value",
            "Another_Field": "Another Value",
        }

    def test_parse_data_empty_values(self):
        """Test parsing data with empty values."""
        config = ParserConfiguration()
        parser = Parser(config)

        data_section = _create_data_section(
            headers=["Sample_ID", "Sample_Name", "Description"],
            data=[
                ["Sample1", "", ""],
                ["Sample2", "Sample Two", ""],
            ],
        )

        parsed_sheet = _create_parsed_sheet(data_section=data_section)

        samples = parser._parse_data(parsed_sheet)

        assert len(samples) == 2

        sample1 = samples[0]
        assert sample1.sample_id == "Sample1"
        assert sample1.sample_name is None
        assert sample1.description is None

        sample2 = samples[1]
        assert sample2.sample_id == "Sample2"
        assert sample2.sample_name == "Sample Two"
        assert sample2.description is None

    def test_parse_data_no_data(self):
        """Test parsing when data section is empty."""
        config = ParserConfiguration()
        parser = Parser(config)

        data_section = _create_data_section()

        parsed_sheet = _create_parsed_sheet(data_section=data_section)

        samples = parser._parse_data(parsed_sheet)

        assert samples == []

    def test_parse_data_missing_sample_id(self):
        """Test parsing fails when required Sample_ID is missing."""
        config = ParserConfiguration()
        parser = Parser(config)

        data_section = _create_data_section(
            headers=["Sample_Name", "Sample_Project"], data=[["Sample One", "Project1"]]
        )

        parsed_sheet = _create_parsed_sheet(data_section=data_section)

        with pytest.raises(ValueError, match="Missing required Sample_ID"):
            parser._parse_data(parsed_sheet)

    def test_parse_data_invalid_lane(self):
        """Test parsing with invalid lane value."""
        config = ParserConfiguration()
        parser = Parser(config)

        data_section = _create_data_section(headers=["Lane", "Sample_ID"], data=[["invalid", "Sample1"]])

        parsed_sheet = _create_parsed_sheet(data_section=data_section)

        samples = parser._parse_data(parsed_sheet)

        assert len(samples) == 1
        assert samples[0].lane is None
        assert samples[0].sample_id == "Sample1"

    def test_parse_data_more_values_than_headers(self):
        """Test parsing data where a row has more values than headers."""
        config = ParserConfiguration()
        parser = Parser(config)

        data_section = _create_data_section(
            headers=["Sample_ID", "Sample_Name"],
            data=[
                ["Sample1", "Sample One", "ExtraValue1", "ExtraValue2"],  # More values than headers
            ],
        )

        parsed_sheet = _create_parsed_sheet(data_section=data_section)

        samples = parser._parse_data(parsed_sheet)

        assert len(samples) == 1
        sample = samples[0]
        assert sample.sample_id == "Sample1"
        assert sample.sample_name == "Sample One"
        # Extra values should be ignored (not stored in extra_metadata since they have no header)

    def test_parse_data_empty_string_normalization(self):
        """Test parsing data with empty string values that get normalized to None."""
        config = ParserConfiguration()
        parser = Parser(config)

        data_section = _create_data_section(
            headers=["Sample_ID", "Sample_Name", "Description"],
            data=[
                ["Sample1", "   ", "Some description"],  # Whitespace-only string that should become None
            ],
        )

        parsed_sheet = _create_parsed_sheet(data_section=data_section)

        samples = parser._parse_data(parsed_sheet)

        assert len(samples) == 1
        sample = samples[0]
        assert sample.sample_id == "Sample1"
        assert sample.sample_name is None  # Whitespace-only string normalized to None
        assert sample.description == "Some description"


class TestParseComplete:
    """Test complete parsing functionality."""

    def test_parse_complete_sample_sheet(self):
        """Test parsing a complete Illumina v1 sample sheet."""
        config = ParserConfiguration()
        parser = Parser(config)

        header_section = HeaderSection(
            name="header",
            rows=[
                HeaderRow(key="IEMFileVersion", value="4"),
                HeaderRow(key="Investigator Name", value="John Doe"),
                HeaderRow(key="Experiment Name", value="Test Experiment"),
                HeaderRow(key="Date", value="2023-01-01"),
                HeaderRow(key="Workflow", value="GenerateFASTQ"),
            ],
        )

        reads_section = HeaderSection(name="reads", rows=[HeaderRow(key="151", value="")])

        data_section = _create_data_section(
            headers=["Sample_ID", "Sample_Name", "I7_Index_ID", "index"],
            data=[
                ["Sample1", "Sample One", "N701", "TAAGGCGA"],
                ["Sample2", "Sample Two", "N702", "CGTACTAG"],
            ],
        )

        parsed_sheet = _create_parsed_sheet(header_sections=[header_section, reads_section], data_section=data_section)

        sample_sheet = parser.parse(parsed_sheet=parsed_sheet)

        assert isinstance(sample_sheet, IlluminaSampleSheet)
        assert sample_sheet.header.iem_file_version == "4"
        assert sample_sheet.header.investigator_name == "John Doe"
        assert sample_sheet.reads is not None
        assert sample_sheet.reads.read_lengths == [151]  # Only one unique value
        assert len(sample_sheet.data) == 2
        assert sample_sheet.data[0].sample_id == "Sample1"
        assert sample_sheet.data[1].sample_id == "Sample2"

    def test_parse_minimal_sample_sheet(self):
        """Test parsing a minimal Illumina v1 sample sheet."""
        config = ParserConfiguration()
        parser = Parser(config)

        header_section = HeaderSection(name="header", rows=[HeaderRow(key="IEMFileVersion", value="4")])

        data_section = _create_data_section(headers=["Sample_ID"], data=[["Sample1"]])

        parsed_sheet = _create_parsed_sheet(header_sections=[header_section], data_section=data_section)

        sample_sheet = parser.parse(parsed_sheet=parsed_sheet)

        assert isinstance(sample_sheet, IlluminaSampleSheet)
        assert sample_sheet.header.iem_file_version == "4"
        assert sample_sheet.reads is None
        assert sample_sheet.settings is None
        assert len(sample_sheet.data) == 1
        assert sample_sheet.data[0].sample_id == "Sample1"


class TestParseFunctionInterface:
    """Test the module-level parse function."""

    def test_parse_function(self):
        """Test the module-level parse function."""
        from elsheeto.parser.illumina_v1 import from_stage2

        config = ParserConfiguration()

        header_section = HeaderSection(
            name="header",
            rows=[
                HeaderRow(key="IEMFileVersion", value="4"),
                HeaderRow(key="Investigator Name", value="John Doe"),
            ],
        )

        data_section = _create_data_section(headers=["Sample_ID"], data=[["Sample1"]])

        parsed_sheet = _create_parsed_sheet(header_sections=[header_section], data_section=data_section)

        sample_sheet = from_stage2(parsed_sheet=parsed_sheet, config=config)

        assert isinstance(sample_sheet, IlluminaSampleSheet)
        assert sample_sheet.header.iem_file_version == "4"
        assert sample_sheet.header.investigator_name == "John Doe"
        assert len(sample_sheet.data) == 1
        assert sample_sheet.data[0].sample_id == "Sample1"
