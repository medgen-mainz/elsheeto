"""Tests for Aviti CSV writer functionality."""

from elsheeto.models.aviti import (
    AvitiRunValues,
    AvitiSample,
    AvitiSettingEntries,
    AvitiSettingEntry,
    AvitiSettings,
    AvitiSheet,
)
from elsheeto.models.utils import CaseInsensitiveDict
from elsheeto.writer.aviti import AvitiCsvWriter
from elsheeto.writer.base import WriterConfiguration


class TestAvitiCsvWriter:
    """Test cases for AvitiCsvWriter."""

    def test_empty_sheet(self):
        """Test writing an empty sheet."""
        sheet = AvitiSheet(samples=[])
        writer = AvitiCsvWriter()

        csv_output = writer.write_to_string(sheet)

        expected_lines = ["[Samples]", "SampleName,Index1,Index2", ""]
        assert csv_output == "\n".join(expected_lines)

    def test_minimal_sheet_with_samples(self):
        """Test writing a minimal sheet with just samples."""
        samples = [
            AvitiSample(sample_name="Sample1", index1="ATCG"),
            AvitiSample(sample_name="Sample2", index1="GCTA", index2="TTTT"),
        ]
        sheet = AvitiSheet(samples=samples)
        writer = AvitiCsvWriter()

        csv_output = writer.write_to_string(sheet)

        expected_lines = ["[Samples]", "SampleName,Index1,Index2", "Sample1,ATCG,", "Sample2,GCTA,TTTT", ""]
        assert csv_output == "\n".join(expected_lines)

    def test_sheet_with_run_values(self):
        """Test writing a sheet with run values."""
        run_values = AvitiRunValues(data=CaseInsensitiveDict({"Experiment": "Test123", "Date": "2024-01-01"}))
        samples = [AvitiSample(sample_name="Sample1", index1="ATCG")]
        sheet = AvitiSheet(run_values=run_values, samples=samples)
        writer = AvitiCsvWriter()

        csv_output = writer.write_to_string(sheet)

        lines = csv_output.split("\n")
        assert "[RunValues]" in lines
        assert "Keyname,Value" in lines
        assert "Experiment,Test123" in lines
        assert "Date,2024-01-01" in lines
        assert "[Samples]" in lines

    def test_sheet_with_settings_no_lanes(self):
        """Test writing a sheet with settings without lane specifications."""
        settings_entries = [
            AvitiSettingEntry(name="ReadLength", value="150"),
            AvitiSettingEntry(name="Cycles", value="300"),
        ]
        settings = AvitiSettings(settings=AvitiSettingEntries(entries=settings_entries))
        samples = [AvitiSample(sample_name="Sample1", index1="ATCG")]
        sheet = AvitiSheet(settings=settings, samples=samples)
        writer = AvitiCsvWriter()

        csv_output = writer.write_to_string(sheet)

        lines = csv_output.split("\n")
        assert "[Settings]" in lines
        assert "SettingName,Value" in lines
        assert "ReadLength,150" in lines
        assert "Cycles,300" in lines

    def test_sheet_with_settings_with_lanes(self):
        """Test writing a sheet with lane-specific settings."""
        settings_entries = [
            AvitiSettingEntry(name="ReadLength", value="150"),
            AvitiSettingEntry(name="Cycles", value="300", lane="1+2"),
            AvitiSettingEntry(name="Adapter", value="ATCG", lane="1"),
        ]
        settings = AvitiSettings(settings=AvitiSettingEntries(entries=settings_entries))
        samples = [AvitiSample(sample_name="Sample1", index1="ATCG")]
        sheet = AvitiSheet(settings=settings, samples=samples)
        writer = AvitiCsvWriter()

        csv_output = writer.write_to_string(sheet)

        lines = csv_output.split("\n")
        assert "[Settings]" in lines
        assert "SettingName,Value,Lane,," in lines
        assert "ReadLength,150,,," in lines
        assert "Cycles,300,1+2,," in lines
        assert "Adapter,ATCG,1,," in lines

    def test_sheet_with_all_sections(self):
        """Test writing a complete sheet with all sections."""
        run_values = AvitiRunValues(data=CaseInsensitiveDict({"Experiment": "FullTest"}))

        settings_entries = [AvitiSettingEntry(name="ReadLength", value="150", lane="1+2")]
        settings = AvitiSettings(settings=AvitiSettingEntries(entries=settings_entries))

        samples = [
            AvitiSample(
                sample_name="Sample1",
                index1="ATCG",
                index2="GCTA",
                lane="1",
                project="ProjectA",
                external_id="EXT001",
                description="Test sample",
            )
        ]

        sheet = AvitiSheet(run_values=run_values, settings=settings, samples=samples)
        writer = AvitiCsvWriter()

        csv_output = writer.write_to_string(sheet)

        # Check section order
        lines = csv_output.split("\n")
        run_values_idx = lines.index("[RunValues]")
        settings_idx = lines.index("[Settings]")
        samples_idx = lines.index("[Samples]")

        assert run_values_idx < settings_idx < samples_idx

        # Check content
        assert "Experiment,FullTest" in lines
        assert "ReadLength,150,1+2,," in lines
        assert "Sample1,ATCG,GCTA,1,ProjectA,EXT001,Test sample" in lines

    def test_samples_with_optional_fields(self):
        """Test writing samples with various optional fields."""
        samples = [
            AvitiSample(sample_name="Sample1", index1="ATCG"),  # Minimal
            AvitiSample(sample_name="Sample2", index1="GCTA", lane="1"),  # With lane
            AvitiSample(sample_name="Sample3", index1="TTTT", project="ProjectA"),  # With project
            AvitiSample(
                sample_name="Sample4",
                index1="AAAA",
                index2="CCCC",
                lane="2",
                project="ProjectB",
                external_id="EXT001",
                description="Full sample",
            ),  # With all fields
        ]

        sheet = AvitiSheet(samples=samples)
        writer = AvitiCsvWriter()

        csv_output = writer.write_to_string(sheet)

        lines = csv_output.split("\n")

        # Should include all optional headers since at least one sample uses each
        header_line = None
        for line in lines:
            if line.startswith("SampleName,"):
                header_line = line
                break

        assert header_line is not None
        headers = header_line.split(",")
        expected_headers = ["SampleName", "Index1", "Index2", "Lane", "Project", "ExternalId", "Description"]
        assert headers == expected_headers

        # Check sample data
        assert "Sample1,ATCG,,,,," in lines
        assert "Sample2,GCTA,,1,,," in lines
        assert "Sample3,TTTT,,,ProjectA,," in lines
        assert "Sample4,AAAA,CCCC,2,ProjectB,EXT001,Full sample" in lines

    def test_samples_with_extra_metadata(self):
        """Test writing samples with extra metadata fields."""
        samples = [
            AvitiSample(
                sample_name="Sample1",
                index1="ATCG",
                extra_metadata=CaseInsensitiveDict({"CustomField": "Value1", "AnotherField": "Value2"}),
            ),
            AvitiSample(
                sample_name="Sample2", index1="GCTA", extra_metadata=CaseInsensitiveDict({"CustomField": "Value3"})
            ),
        ]

        sheet = AvitiSheet(samples=samples)
        writer = AvitiCsvWriter()

        csv_output = writer.write_to_string(sheet)

        lines = csv_output.split("\n")

        # Find header line
        header_line = None
        for line in lines:
            if line.startswith("SampleName,"):
                header_line = line
                break

        assert header_line is not None
        headers = header_line.split(",")

        # Should include extra metadata columns in sorted order
        assert "AnotherField" in headers
        assert "CustomField" in headers

        # Check that extra columns come after standard ones
        standard_headers = ["SampleName", "Index1", "Index2"]
        for i, header in enumerate(headers[: len(standard_headers)]):
            assert header == standard_headers[i]

    def test_composite_indices(self):
        """Test writing samples with composite indices."""
        samples = [
            AvitiSample(sample_name="Sample1", index1="ATCG+GCTA", index2="TTTT+AAAA"),
            AvitiSample(sample_name="Sample2", index1="CCCC+GGGG+TTTT", index2=""),
        ]

        sheet = AvitiSheet(samples=samples)
        writer = AvitiCsvWriter()

        csv_output = writer.write_to_string(sheet)

        lines = csv_output.split("\n")
        assert "Sample1,ATCG+GCTA,TTTT+AAAA" in lines
        assert "Sample2,CCCC+GGGG+TTTT," in lines

    def test_writer_configuration_no_empty_lines(self):
        """Test writer configuration without empty lines."""
        config = WriterConfiguration(include_empty_lines=False)

        run_values = AvitiRunValues(data=CaseInsensitiveDict({"Key": "Value"}))
        settings_entries = [AvitiSettingEntry(name="Setting", value="Value")]
        settings = AvitiSettings(settings=AvitiSettingEntries(entries=settings_entries))
        samples = [AvitiSample(sample_name="Sample1", index1="ATCG")]

        sheet = AvitiSheet(run_values=run_values, settings=settings, samples=samples)
        writer = AvitiCsvWriter(config)

        csv_output = writer.write_to_string(sheet)

        # Should not have empty lines between sections
        lines = csv_output.split("\n")

        # Find section indices
        run_values_idx = lines.index("[RunValues]")
        lines.index("[Settings]")
        lines.index("[Samples]")

        # Check no empty lines between sections - just verify sections are contiguous
        # Content between RunValues and Settings: header line + content line
        assert lines[run_values_idx + 1] == "Keyname,Value"
        assert lines[run_values_idx + 2] == "Key,Value"
        assert lines[run_values_idx + 3] == "[Settings]"

    def test_empty_sections(self):
        """Test writing with empty sections."""
        # Empty run values (should be skipped)
        run_values = AvitiRunValues(data=CaseInsensitiveDict({}))

        # Empty settings (should be skipped)
        settings = AvitiSettings(settings=AvitiSettingEntries(entries=[]))

        samples = [AvitiSample(sample_name="Sample1", index1="ATCG")]

        sheet = AvitiSheet(run_values=run_values, settings=settings, samples=samples)
        writer = AvitiCsvWriter()

        csv_output = writer.write_to_string(sheet)

        lines = csv_output.split("\n")

        # Should not include RunValues section (empty data)
        assert "[RunValues]" not in lines

        # Should not include Settings section (empty entries)
        assert "[Settings]" not in lines

        # Should include Samples section
        assert "[Samples]" in lines

    def test_case_insensitive_data(self):
        """Test that case-insensitive data is preserved correctly."""
        run_values = AvitiRunValues(
            data=CaseInsensitiveDict({"ExperimentName": "Test", "experimentdate": "2024-01-01"})
        )

        samples = [AvitiSample(sample_name="Sample1", index1="ATCG")]
        sheet = AvitiSheet(run_values=run_values, samples=samples)
        writer = AvitiCsvWriter()

        csv_output = writer.write_to_string(sheet)

        # Should preserve original key casing
        assert "ExperimentName,Test" in csv_output
        assert "experimentdate,2024-01-01" in csv_output
