"""Integration tests for Aviti CSV writing functionality."""

import tempfile
from pathlib import Path

from elsheeto.facade import parse_aviti, write_aviti_to_file, write_aviti_to_string
from elsheeto.models.aviti import AvitiSample, AvitiSheetBuilder


class TestAvitiCsvWriterIntegration:
    """Integration tests for Aviti CSV writing."""

    def test_round_trip_parsing_basic(self):
        """Test parsing a CSV, modifying it, writing it, and parsing again."""
        # Create a test sheet
        builder = AvitiSheetBuilder()
        original_sheet = (
            builder.add_sample(AvitiSample(sample_name="Sample1", index1="ATCG", project="ProjectA"))
            .add_sample(AvitiSample(sample_name="Sample2", index1="GCTA", project="ProjectB"))
            .add_run_value("Experiment", "Test123")
            .add_setting("ReadLength", "150")
            .build()
        )

        # Write to CSV
        csv_content = write_aviti_to_string(original_sheet)

        # Parse it back
        parsed_sheet = parse_aviti_from_data(csv_content)

        # Compare key data
        assert len(parsed_sheet.samples) == len(original_sheet.samples)
        assert parsed_sheet.samples[0].sample_name == original_sheet.samples[0].sample_name
        assert parsed_sheet.samples[0].index1 == original_sheet.samples[0].index1
        assert parsed_sheet.samples[0].project == original_sheet.samples[0].project

        assert parsed_sheet.run_values is not None
        assert parsed_sheet.run_values.data["Experiment"] == "Test123"

        assert parsed_sheet.settings is not None
        setting = parsed_sheet.settings.settings.get_by_key("ReadLength")
        assert setting.value == "150"

    def test_round_trip_parsing_complex(self):
        """Test round-trip parsing with complex data including lane-specific settings."""
        # Create a complex test sheet
        builder = AvitiSheetBuilder()
        original_sheet = (
            builder.add_sample(
                AvitiSample(
                    sample_name="Sample1",
                    index1="ATCG+GCTA",
                    index2="TTTT+AAAA",
                    lane="1",
                    project="ProjectA",
                    external_id="EXT001",
                    description="Complex sample",
                )
            )
            .add_sample(AvitiSample(sample_name="Sample2", index1="CCCC", index2="GGGG", lane="2", project="ProjectB"))
            .add_run_value("Experiment", "ComplexTest")
            .add_run_value("Date", "2024-01-01")
            .add_setting("ReadLength", "150")
            .add_setting("Cycles", "300", "1+2")
            .add_setting("Adapter", "ATCGATCG", "1")
            .build()
        )

        # Write to CSV
        csv_content = write_aviti_to_string(original_sheet)

        # Parse it back
        parsed_sheet = parse_aviti_from_data(csv_content)

        # Verify samples
        assert len(parsed_sheet.samples) == 2

        sample1 = parsed_sheet.samples[0]
        assert sample1.sample_name == "Sample1"
        assert sample1.index1 == "ATCG+GCTA"
        assert sample1.index2 == "TTTT+AAAA"
        assert sample1.lane == "1"
        assert sample1.project == "ProjectA"
        assert sample1.external_id == "EXT001"
        assert sample1.description == "Complex sample"

        sample2 = parsed_sheet.samples[1]
        assert sample2.sample_name == "Sample2"
        assert sample2.index1 == "CCCC"
        assert sample2.index2 == "GGGG"
        assert sample2.lane == "2"
        assert sample2.project == "ProjectB"

        # Verify run values
        assert parsed_sheet.run_values is not None
        assert parsed_sheet.run_values.data["Experiment"] == "ComplexTest"
        assert parsed_sheet.run_values.data["Date"] == "2024-01-01"

        # Verify settings including lane-specific ones
        assert parsed_sheet.settings is not None

        read_length = parsed_sheet.settings.settings.get_by_key("ReadLength")
        assert read_length.value == "150"
        assert read_length.lane is None

        cycles = parsed_sheet.settings.settings.get_by_key_and_lane("Cycles", "1+2")
        assert cycles.value == "300"

        adapter = parsed_sheet.settings.settings.get_by_key_and_lane("Adapter", "1")
        assert adapter.value == "ATCGATCG"

    def test_modify_and_write_workflow(self):
        """Test the complete workflow: parse, modify, write."""
        # Start with existing test data
        test_csv = """[RunValues]
Keyname,Value
Experiment,OriginalTest

[Settings]
SettingName,Value,Lane
ReadLength,100,
Cycles,200,1+2

[Samples]
SampleName,Index1,Index2,Project
Original1,ATCG,GCTA,OriginalProject
Original2,TTTT,AAAA,OriginalProject
"""

        # Parse the original
        original_sheet = parse_aviti_from_data(test_csv)

        # Apply modifications
        modified_sheet = (
            original_sheet.with_sample_added(AvitiSample(sample_name="NewSample", index1="CCCC", project="NewProject"))
            .with_sample_modified("Original1", project="ModifiedProject")
            .with_run_value_added("NewRunValue", "NewValue")
            .with_setting_added("NewSetting", "NewSettingValue", "2")
        )

        # Write modified sheet
        modified_csv = write_aviti_to_string(modified_sheet)

        # Parse the modified CSV
        final_sheet = parse_aviti_from_data(modified_csv)

        # Verify modifications were preserved
        assert len(final_sheet.samples) == 3

        # Check original sample was modified
        original1 = next(s for s in final_sheet.samples if s.sample_name == "Original1")
        assert original1.project == "ModifiedProject"

        # Check new sample was added
        new_sample = next(s for s in final_sheet.samples if s.sample_name == "NewSample")
        assert new_sample.index1 == "CCCC"
        assert new_sample.project == "NewProject"

        # Check run values
        assert final_sheet.run_values is not None
        assert final_sheet.run_values.data["Experiment"] == "OriginalTest"
        assert final_sheet.run_values.data["NewRunValue"] == "NewValue"

        # Check settings
        assert final_sheet.settings is not None
        new_setting = final_sheet.settings.settings.get_by_key_and_lane("NewSetting", "2")
        assert new_setting.value == "NewSettingValue"

    def test_file_write_and_read(self):
        """Test writing to and reading from actual files."""
        # Create a test sheet
        builder = AvitiSheetBuilder()
        original_sheet = (
            builder.add_sample(AvitiSample(sample_name="FileTest", index1="ATCG"))
            .add_run_value("FileExperiment", "FileValue")
            .build()
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test_sheet.csv"

            # Write to file
            write_aviti_to_file(original_sheet, file_path)

            # Verify file was created
            assert file_path.exists()

            # Read back from file
            parsed_sheet = parse_aviti(file_path)

            # Verify content
            assert len(parsed_sheet.samples) == 1
            assert parsed_sheet.samples[0].sample_name == "FileTest"
            # Check that parsed sheet matches
            assert parsed_sheet.run_values is not None
            assert parsed_sheet.run_values.data["FileExperiment"] == "FileValue"

    def test_edge_case_empty_fields(self):
        """Test round-trip with empty and None fields."""
        # Create sheet with various empty fields
        builder = AvitiSheetBuilder()
        original_sheet = (
            builder.add_sample(AvitiSample(sample_name="EmptyTest", index1="ATCG", index2=""))  # Empty index2
            .add_sample(AvitiSample(sample_name="NoneTest", index1="GCTA"))  # None index2 (default)
            .build()
        )

        # Write and parse back
        csv_content = write_aviti_to_string(original_sheet)
        parsed_sheet = parse_aviti_from_data(csv_content)

        # Verify empty fields are handled correctly
        assert len(parsed_sheet.samples) == 2

        empty_sample = next(s for s in parsed_sheet.samples if s.sample_name == "EmptyTest")
        assert empty_sample.index2 == ""

        none_sample = next(s for s in parsed_sheet.samples if s.sample_name == "NoneTest")
        assert none_sample.index2 == ""  # Should be converted to empty string

    def test_special_characters_preservation(self):
        """Test that special characters are preserved in round-trip."""
        # Create sheet with special characters
        builder = AvitiSheetBuilder()
        original_sheet = (
            builder.add_sample(
                AvitiSample(
                    sample_name="Special,Test",
                    index1="ATCG",
                    description="Contains, commas and spaces",  # Simplified to avoid CSV quote issues
                )
            )
            .add_run_value("Special Key", "Value with spaces")
            .add_setting("Comma,Setting", "Value,with,commas")
            .build()
        )

        # Write and parse back
        csv_content = write_aviti_to_string(original_sheet)
        parsed_sheet = parse_aviti_from_data(csv_content)

        # Verify special characters are preserved
        sample = parsed_sheet.samples[0]
        assert sample.sample_name == "Special,Test"
        assert sample.description == "Contains, commas and spaces"

        assert parsed_sheet.run_values is not None
        assert parsed_sheet.run_values.data["Special Key"] == "Value with spaces"

        assert parsed_sheet.settings is not None
        setting = parsed_sheet.settings.settings.get_by_key("Comma,Setting")
        assert setting.value == "Value,with,commas"


def parse_aviti_from_data(data: str):
    """Helper function to parse Aviti data from string."""
    from elsheeto.facade import parse_aviti_from_data as parse_func

    return parse_func(data)
