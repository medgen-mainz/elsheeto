"""Tests for IlluminaCsvWriter functionality."""

import io

from elsheeto.models.illumina_v1 import (
    IlluminaHeader,
    IlluminaReads,
    IlluminaSample,
    IlluminaSampleSheet,
    IlluminaSettings,
)
from elsheeto.models.utils import CaseInsensitiveDict
from elsheeto.writer.base import WriterConfiguration
from elsheeto.writer.illumina_v1 import IlluminaCsvWriter


class TestIlluminaCsvWriter:
    """Test cases for IlluminaCsvWriter."""

    def test_writer_initialization_default_config(self):
        """Test writer initialization with default configuration."""
        writer = IlluminaCsvWriter()
        assert writer.config.include_empty_lines is True
        assert writer.config.csv_dialect == "excel"

    def test_writer_initialization_custom_config(self):
        """Test writer initialization with custom configuration."""
        config = WriterConfiguration(include_empty_lines=False, csv_dialect="unix")
        writer = IlluminaCsvWriter(config)
        assert writer.config.include_empty_lines is False
        assert writer.config.csv_dialect == "unix"

    def test_write_to_string_minimal_sheet(self):
        """Test writing a minimal sheet to string."""
        header = IlluminaHeader()
        sheet = IlluminaSampleSheet(header=header, reads=None, settings=None, data=[])

        writer = IlluminaCsvWriter()
        result = writer.write_to_string(sheet)

        # Should contain header section even if minimal
        assert "[Header]" in result
        assert "Workflow,GenerateFASTQ" in result

    def test_write_to_string_complete_sheet(self):
        """Test writing a complete sheet with all sections."""
        # Create complete header with extra metadata
        header = IlluminaHeader(
            iem_file_version="5",
            investigator_name="Test Investigator",
            experiment_name="Test Experiment",
            date="2024-01-01",
            workflow="GenerateFASTQ",
            application="FASTQ Only",
            extra_metadata=CaseInsensitiveDict({"CustomField": "CustomValue"}),
        )

        # Create reads
        reads = IlluminaReads(read_lengths=[150, 150])

        # Create settings
        settings = IlluminaSettings(
            data=CaseInsensitiveDict({"Setting1": "Value1", "Setting2": "Value2"}),
            extra_metadata=CaseInsensitiveDict({"ExtraSet": "ExtraVal"}),
        )

        # Create samples with various field combinations
        samples = [
            IlluminaSample(
                lane=1,
                sample_id="Sample1",
                sample_name="Test Sample 1",
                sample_plate="Plate1",
                sample_well="A01",
                index="ATCG",
                index2="GCTA",
                sample_project="Project1",
                description="Test sample",
                extra_metadata=CaseInsensitiveDict({"Custom": "Value1"}),
            ),
            IlluminaSample(sample_id="Sample2", sample_name="Test Sample 2", index="TTTT", sample_project="Project2"),
        ]

        sheet = IlluminaSampleSheet(header=header, reads=reads, settings=settings, data=samples)

        writer = IlluminaCsvWriter()
        result = writer.write_to_string(sheet)

        # Check all sections are present
        assert "[Header]" in result
        assert "[Reads]" in result
        assert "[Settings]" in result
        assert "[Data]" in result

        # Check header content
        assert "IEMFileVersion,5" in result
        assert "Investigator Name,Test Investigator" in result
        assert "CustomField,CustomValue" in result

        # Check reads content
        assert "150" in result

        # Check settings content
        assert "Setting1,Value1" in result
        assert "Setting2,Value2" in result

        # Check data content
        assert "Sample1" in result
        assert "Sample2" in result
        assert "Test Sample 1" in result
        assert "ATCG" in result

    def test_write_to_file(self, tmp_path):
        """Test writing to file."""
        header = IlluminaHeader(experiment_name="File Test")
        samples = [IlluminaSample(sample_id="S1", sample_name="Sample1")]
        sheet = IlluminaSampleSheet(header=header, reads=None, settings=None, data=samples)

        output_file = tmp_path / "test_output.csv"
        writer = IlluminaCsvWriter()
        writer.write_to_file(sheet, output_file)

        assert output_file.exists()
        content = output_file.read_text()
        assert "[Header]" in content
        assert "Experiment Name,File Test" in content
        assert "Sample1" in content

    def test_section_header_formatting(self):
        """Test section header formatting with trailing commas."""
        writer = IlluminaCsvWriter()
        output = io.StringIO()
        csv_writer = writer._create_csv_writer(output)

        writer._write_section_header(csv_writer, "TestSection")
        result = output.getvalue()

        # Should have section name in brackets followed by trailing commas
        assert "[TestSection]" in result
        assert result.count(",") >= 10  # Should have trailing commas

    def test_header_section_empty_extra_metadata(self):
        """Test header section with no extra metadata."""
        header = IlluminaHeader(experiment_name="Test")
        sheet = IlluminaSampleSheet(header=header, reads=None, settings=None, data=[])

        writer = IlluminaCsvWriter()
        result = writer.write_to_string(sheet)

        assert "Experiment Name,Test" in result
        # Should not have extra metadata lines
        lines = result.split("\n")
        header_lines = []
        in_header = False
        for line in lines:
            if line.startswith("[Header]"):
                in_header = True
                continue
            elif line.startswith("[") and in_header:
                break
            elif in_header and line.strip():
                header_lines.append(line)

        # Should only have standard header fields, no extra metadata
        # Note: Ignore lines that are just trailing commas (empty lines in Illumina format)
        extra_metadata_lines = []
        for line in header_lines:
            # Skip if it's a standard header field
            if any(
                field in line
                for field in [
                    "IEMFileVersion",
                    "Investigator Name",
                    "Experiment Name",
                    "Date",
                    "Workflow",
                    "Application",
                    "Instrument Type",
                    "Assay",
                    "Index Adapters",
                    "Description",
                    "Chemistry",
                    "Run",
                ]
            ):
                continue
            # Skip if it's just trailing commas
            if line.strip().replace(",", "") == "":
                continue
            # This is an extra metadata line
            extra_metadata_lines.append(line)

        assert len(extra_metadata_lines) == 0

    def test_reads_section_empty(self):
        """Test reads section when no reads are specified."""
        header = IlluminaHeader()
        sheet = IlluminaSampleSheet(header=header, reads=None, settings=None, data=[])

        writer = IlluminaCsvWriter()
        result = writer.write_to_string(sheet)

        # Should still have reads section header but no content
        assert "[Reads]" in result
        lines = result.split("\n")
        reads_idx = next(i for i, line in enumerate(lines) if line.startswith("[Reads]"))

        # Next non-empty line should be next section or end
        next_content_idx = reads_idx + 1
        while next_content_idx < len(lines) and not lines[next_content_idx].strip():
            next_content_idx += 1

        if next_content_idx < len(lines):
            # Should be next section header or empty line with trailing commas
            next_line = lines[next_content_idx]
            assert (
                next_line.startswith("[") or not next_line.strip() or next_line.strip().replace(",", "") == ""
            )  # Empty line with trailing commas

    def test_settings_section_empty(self):
        """Test settings section when no settings are specified."""
        header = IlluminaHeader()
        sheet = IlluminaSampleSheet(header=header, reads=None, settings=None, data=[])

        writer = IlluminaCsvWriter()
        result = writer.write_to_string(sheet)

        # Should still have settings section header but no content
        assert "[Settings]" in result

    def test_data_section_with_lanes(self):
        """Test data section includes Lane column when samples have lanes."""
        header = IlluminaHeader()
        samples = [
            IlluminaSample(lane=1, sample_id="S1", sample_name="Sample1"),
            IlluminaSample(lane=2, sample_id="S2", sample_name="Sample2"),
        ]
        sheet = IlluminaSampleSheet(header=header, reads=None, settings=None, data=samples)

        writer = IlluminaCsvWriter()
        result = writer.write_to_string(sheet)

        # Should include Lane column
        assert "Lane" in result
        assert "1" in result
        assert "2" in result

    def test_data_section_without_lanes(self):
        """Test data section excludes Lane column when no samples have lanes."""
        header = IlluminaHeader()
        samples = [
            IlluminaSample(sample_id="S1", sample_name="Sample1"),
            IlluminaSample(sample_id="S2", sample_name="Sample2"),
        ]
        sheet = IlluminaSampleSheet(header=header, reads=None, settings=None, data=samples)

        writer = IlluminaCsvWriter()
        result = writer.write_to_string(sheet)

        # Check data section header - should not include Lane
        lines = result.split("\n")
        data_idx = next(i for i, line in enumerate(lines) if line.startswith("[Data]"))
        header_line = lines[data_idx + 1]  # First line after [Data] should be headers

        # Should not have Lane column if no samples have lanes
        assert "Lane" not in header_line

    def test_data_section_extra_metadata_fields(self):
        """Test data section includes extra metadata fields."""
        header = IlluminaHeader()
        samples = [
            IlluminaSample(
                sample_id="S1",
                sample_name="Sample1",
                extra_metadata=CaseInsensitiveDict({"CustomField1": "Value1", "CustomField2": "Value2"}),
            ),
            IlluminaSample(
                sample_id="S2",
                sample_name="Sample2",
                extra_metadata=CaseInsensitiveDict({"CustomField1": "Value3", "CustomField3": "Value4"}),
            ),
        ]
        sheet = IlluminaSampleSheet(header=header, reads=None, settings=None, data=samples)

        writer = IlluminaCsvWriter()
        result = writer.write_to_string(sheet)

        # Should include all extra metadata fields
        assert "CustomField1" in result
        assert "CustomField2" in result
        assert "CustomField3" in result
        assert "Value1" in result
        assert "Value2" in result
        assert "Value3" in result
        assert "Value4" in result

    def test_data_section_field_ordering(self):
        """Test that data section fields are in correct order."""
        header = IlluminaHeader()
        samples = [
            IlluminaSample(
                lane=1,
                sample_id="S1",
                sample_name="Sample1",
                sample_plate="Plate1",
                sample_well="A01",
                index="ATCG",
                sample_project="Project1",
            )
        ]
        sheet = IlluminaSampleSheet(header=header, reads=None, settings=None, data=samples)

        writer = IlluminaCsvWriter()
        result = writer.write_to_string(sheet)

        # Find the data header line
        lines = result.split("\n")
        data_idx = next(i for i, line in enumerate(lines) if line.startswith("[Data]"))
        header_line = lines[data_idx + 1]

        # Sample_ID should be included (core field)
        assert "Sample_ID" in header_line
        # Lane should be first since sample has lane
        assert header_line.startswith("Lane,")

    def test_config_include_empty_lines_false(self):
        """Test configuration with include_empty_lines=False."""
        config = WriterConfiguration(include_empty_lines=False)
        writer = IlluminaCsvWriter(config)

        header = IlluminaHeader(experiment_name="Test")
        sheet = IlluminaSampleSheet(header=header, reads=None, settings=None, data=[])

        result = writer.write_to_string(sheet)

        # Should have fewer empty lines
        lines = result.split("\n")
        empty_lines = [line for line in lines if not line.strip()]

        # With include_empty_lines=False, should have minimal empty lines
        assert len(empty_lines) < 5  # Should be significantly fewer

    def test_empty_data_section(self):
        """Test data section when no samples are provided."""
        header = IlluminaHeader()
        sheet = IlluminaSampleSheet(header=header, reads=None, settings=None, data=[])

        writer = IlluminaCsvWriter()
        result = writer.write_to_string(sheet)

        # Should still have data section header
        assert "[Data]" in result

        # Find data section
        lines = result.split("\n")
        data_idx = next(i for i, line in enumerate(lines) if line.startswith("[Data]"))

        # Should not have data rows, only section header
        remaining_lines = lines[data_idx + 1 :]
        non_empty_lines = [line for line in remaining_lines if line.strip()]
        assert len(non_empty_lines) == 0

    def test_none_values_handling(self):
        """Test handling of None values in sample fields."""
        header = IlluminaHeader()
        samples = [
            IlluminaSample(
                sample_id="S1",
                sample_name=None,  # None value
                sample_plate="Plate1",
                sample_well=None,  # None value
                index="ATCG",
            )
        ]
        sheet = IlluminaSampleSheet(header=header, reads=None, settings=None, data=samples)

        writer = IlluminaCsvWriter()
        result = writer.write_to_string(sheet)

        # None values should be represented as empty strings
        lines = result.split("\n")
        data_lines = []
        in_data = False
        for line in lines:
            if line.startswith("[Data]"):
                in_data = True
                continue
            elif line.startswith("[") and in_data:
                break
            elif in_data and line.strip():
                data_lines.append(line)

        # Should have header line and one data line
        assert len(data_lines) == 2
        data_row = data_lines[1]  # Second line is the actual data

        # Check that None values appear as empty fields
        fields = data_row.split(",")
        # Sample_ID should be S1, other None fields should be empty
        assert "S1" in fields
