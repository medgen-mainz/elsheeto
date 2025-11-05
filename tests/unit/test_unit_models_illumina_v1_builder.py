"""Tests for IlluminaSheetBuilder functionality."""

import pytest

from elsheeto.models.illumina_v1 import (
    IlluminaHeader,
    IlluminaReads,
    IlluminaSample,
    IlluminaSampleSheet,
    IlluminaSettings,
    IlluminaSheetBuilder,
)
from elsheeto.models.utils import CaseInsensitiveDict


class TestIlluminaSheetBuilder:
    """Test cases for IlluminaSheetBuilder."""

    def test_empty_builder_initialization(self):
        """Test creating an empty builder."""
        builder = IlluminaSheetBuilder()
        sheet = builder.build()

        # Header is always present (required by model) but with default values
        assert sheet.header is not None
        assert sheet.header.workflow == "GenerateFASTQ"  # Default value
        assert sheet.header.experiment_name is None  # No custom value set
        assert sheet.reads is None
        assert sheet.settings is None
        assert sheet.data == []

    def test_from_sheet_initialization(self):
        """Test creating a builder from an existing sheet."""
        # Create a sample sheet
        sample = IlluminaSample(sample_id="Test", sample_name="Test", index="ATCG")
        header = IlluminaHeader(
            iem_file_version="5",
            experiment_name="Test",
            date="2024-01-01",
            workflow="GenerateFASTQ",
            extra_metadata=CaseInsensitiveDict({"Application": "App"}),
        )
        reads = IlluminaReads(read_lengths=[150, 150])
        settings = IlluminaSettings(
            data=CaseInsensitiveDict({"Setting": "Value"}), extra_metadata=CaseInsensitiveDict()
        )

        original_sheet = IlluminaSampleSheet(header=header, reads=reads, settings=settings, data=[sample])

        # Create builder from sheet
        builder = IlluminaSheetBuilder.from_sheet(original_sheet)
        rebuilt_sheet = builder.build()

        assert len(rebuilt_sheet.data) == 1
        assert rebuilt_sheet.data[0].sample_name == "Test"
        assert rebuilt_sheet.header is not None
        assert rebuilt_sheet.header.experiment_name == "Test"
        assert rebuilt_sheet.reads is not None
        assert rebuilt_sheet.reads.read_lengths == [150, 150]
        assert rebuilt_sheet.settings is not None
        assert rebuilt_sheet.settings.data["Setting"] == "Value"

    def test_add_sample(self):
        """Test adding a single sample."""
        builder = IlluminaSheetBuilder()
        sample = IlluminaSample(sample_id="Sample1", sample_name="Sample1", index="ATCG")

        builder.add_sample(sample)
        sheet = builder.build()

        assert len(sheet.data) == 1
        assert sheet.data[0].sample_name == "Sample1"

    def test_add_multiple_samples(self):
        """Test adding multiple samples."""
        builder = IlluminaSheetBuilder()
        sample1 = IlluminaSample(sample_id="Sample1", sample_name="Sample1", index="ATCG")
        sample2 = IlluminaSample(sample_id="Sample2", sample_name="Sample2", index="GCTA")

        builder.add_sample(sample1).add_sample(sample2)
        sheet = builder.build()

        assert len(sheet.data) == 2
        assert sheet.data[0].sample_name == "Sample1"
        assert sheet.data[1].sample_name == "Sample2"

    def test_add_samples_bulk(self):
        """Test adding multiple samples at once."""
        builder = IlluminaSheetBuilder()
        samples = [
            IlluminaSample(sample_id="Sample1", sample_name="Sample1", index="ATCG"),
            IlluminaSample(sample_id="Sample2", sample_name="Sample2", index="GCTA"),
        ]

        builder.add_samples(samples)
        sheet = builder.build()

        assert len(sheet.data) == 2
        assert sheet.data[0].sample_name == "Sample1"
        assert sheet.data[1].sample_name == "Sample2"

    def test_remove_sample_by_id(self):
        """Test removing a sample by ID."""
        builder = IlluminaSheetBuilder()
        sample1 = IlluminaSample(sample_id="Sample1", sample_name="Sample1", index="ATCG")
        sample2 = IlluminaSample(sample_id="Sample2", sample_name="Sample2", index="GCTA")

        builder.add_sample(sample1).add_sample(sample2)
        builder.remove_sample("Sample1")
        sheet = builder.build()

        assert len(sheet.data) == 1
        assert sheet.data[0].sample_name == "Sample2"

    def test_remove_sample_by_index(self):
        """Test removing a sample by index."""
        builder = IlluminaSheetBuilder()
        sample1 = IlluminaSample(sample_id="Sample1", sample_name="Sample1", index="ATCG")
        sample2 = IlluminaSample(sample_id="Sample2", sample_name="Sample2", index="GCTA")

        builder.add_sample(sample1).add_sample(sample2)
        builder.remove_sample(0)
        sheet = builder.build()

        assert len(sheet.data) == 1
        assert sheet.data[0].sample_name == "Sample2"

    def test_remove_sample_nonexistent_id(self):
        """Test removing a non-existent sample by ID."""
        builder = IlluminaSheetBuilder()
        sample = IlluminaSample(sample_id="Sample1", sample_name="Sample1", index="ATCG")
        builder.add_sample(sample)

        with pytest.raises(ValueError, match="Sample with ID 'NonExistent' not found"):
            builder.remove_sample("NonExistent")

    def test_remove_sample_invalid_index(self):
        """Test removing a sample with invalid index."""
        builder = IlluminaSheetBuilder()
        sample = IlluminaSample(sample_id="Sample1", sample_name="Sample1", index="ATCG")
        builder.add_sample(sample)

        with pytest.raises(IndexError, match="Sample index 5 is out of range"):
            builder.remove_sample(5)

    def test_update_sample_by_id(self):
        """Test updating a sample by ID."""
        builder = IlluminaSheetBuilder()
        sample = IlluminaSample(sample_id="Sample1", sample_name="Sample1", index="ATCG")
        builder.add_sample(sample)

        builder.update_sample("Sample1", sample_name="UpdatedSample", sample_project="NewProject")
        sheet = builder.build()

        assert sheet.data[0].sample_name == "UpdatedSample"
        assert sheet.data[0].sample_project == "NewProject"
        assert sheet.data[0].sample_id == "Sample1"  # ID preserved

    def test_update_sample_by_index(self):
        """Test updating a sample by index."""
        builder = IlluminaSheetBuilder()
        sample = IlluminaSample(sample_id="Sample1", sample_name="Sample1", index="ATCG")
        builder.add_sample(sample)

        builder.update_sample(0, sample_name="UpdatedSample", index="GGGG")
        sheet = builder.build()

        assert sheet.data[0].sample_name == "UpdatedSample"
        assert sheet.data[0].index == "GGGG"
        assert sheet.data[0].sample_id == "Sample1"  # ID preserved

    def test_update_sample_nonexistent_id(self):
        """Test updating a non-existent sample by ID."""
        builder = IlluminaSheetBuilder()
        sample = IlluminaSample(sample_id="Sample1", sample_name="Sample1", index="ATCG")
        builder.add_sample(sample)

        with pytest.raises(ValueError, match="Sample with ID 'NonExistent' not found"):
            builder.update_sample("NonExistent", sample_name="Updated")

    def test_update_sample_invalid_field(self):
        """Test updating a sample with invalid field."""
        builder = IlluminaSheetBuilder()
        sample = IlluminaSample(sample_id="Sample1", sample_name="Sample1", index="ATCG")
        builder.add_sample(sample)

        with pytest.raises(ValueError, match="Invalid field 'invalid_field' for IlluminaSample"):
            builder.update_sample("Sample1", invalid_field="value")

    def test_clear_samples(self):
        """Test clearing all samples."""
        builder = IlluminaSheetBuilder()
        sample1 = IlluminaSample(sample_id="Sample1", sample_name="Sample1", index="ATCG")
        sample2 = IlluminaSample(sample_id="Sample2", sample_name="Sample2", index="GCTA")

        builder.add_sample(sample1).add_sample(sample2)
        assert len(builder._samples) == 2

        builder.clear_samples()
        sheet = builder.build()

        assert len(sheet.data) == 0

    def test_set_header(self):
        """Test setting header."""
        builder = IlluminaSheetBuilder()
        header = IlluminaHeader(
            iem_file_version="5",
            experiment_name="TestExperiment",
            date="2024-01-01",
            workflow="GenerateFASTQ",
            extra_metadata=CaseInsensitiveDict(),
        )

        builder.set_header(header)
        sheet = builder.build()

        assert sheet.header is not None
        assert sheet.header.experiment_name == "TestExperiment"
        assert sheet.header.iem_file_version == "5"

    def test_update_header_field(self):
        """Test updating a header field."""
        builder = IlluminaSheetBuilder()
        header = IlluminaHeader(
            iem_file_version="5",
            experiment_name="Original",
            date="2024-01-01",
            workflow="GenerateFASTQ",
            extra_metadata=CaseInsensitiveDict({"App": "Original"}),
        )
        builder.set_header(header)

        builder.update_header_field("experiment_name", "Updated")
        builder.update_header_field("App", "UpdatedApp")
        sheet = builder.build()

        assert sheet.header.experiment_name == "Updated"
        assert sheet.header.extra_metadata["App"] == "UpdatedApp"

    def test_update_header_field_no_header(self):
        """Test updating a header field when no header is set."""
        builder = IlluminaSheetBuilder()

        with pytest.raises(ValueError, match="No header set. Use set_header\\(\\) first"):
            builder.update_header_field("experiment_name", "Updated")

    def test_set_reads(self):
        """Test setting reads."""
        builder = IlluminaSheetBuilder()
        reads = IlluminaReads(read_lengths=[150, 150])

        builder.set_reads(reads)
        sheet = builder.build()

        assert sheet.reads is not None
        assert sheet.reads.read_lengths == [150, 150]

    def test_update_reads(self):
        """Test updating read lengths."""
        builder = IlluminaSheetBuilder()
        reads = IlluminaReads(read_lengths=[100, 100])
        builder.set_reads(reads)

        builder.update_reads([75, 75, 50])
        sheet = builder.build()

        assert sheet.reads is not None
        assert sheet.reads.read_lengths == [75, 75, 50]

    def test_update_reads_no_reads_set(self):
        """Test updating reads when no reads are set."""
        builder = IlluminaSheetBuilder()

        with pytest.raises(ValueError, match="No reads set. Use set_reads\\(\\) first"):
            builder.update_reads([150])

    def test_set_settings(self):
        """Test setting settings."""
        builder = IlluminaSheetBuilder()
        settings = IlluminaSettings(
            data=CaseInsensitiveDict(), extra_metadata=CaseInsensitiveDict({"Setting1": "Value1"})
        )

        builder.set_settings(settings)
        sheet = builder.build()

        assert sheet.settings is not None
        assert sheet.settings.extra_metadata["Setting1"] == "Value1"

    def test_update_settings_field(self):
        """Test updating a settings field."""
        builder = IlluminaSheetBuilder()
        settings = IlluminaSettings(
            data=CaseInsensitiveDict({"Setting1": "Original"}), extra_metadata=CaseInsensitiveDict()
        )
        builder.set_settings(settings)

        builder.update_settings_field("Setting1", "Updated")
        builder.update_settings_field("NewSetting", "NewValue")
        sheet = builder.build()

        assert sheet.settings is not None
        assert sheet.settings.data["Setting1"] == "Updated"
        assert sheet.settings.data["NewSetting"] == "NewValue"

    def test_update_settings_field_no_settings(self):
        """Test updating a settings field when no settings are set."""
        builder = IlluminaSheetBuilder()

        with pytest.raises(ValueError, match="No settings set. Use set_settings\\(\\) first"):
            builder.update_settings_field("Setting1", "Value")

    def test_complex_building_scenario(self):
        """Test a complex building scenario with all components."""
        builder = IlluminaSheetBuilder()

        # Set header
        header = IlluminaHeader(
            iem_file_version="5",
            experiment_name="ComplexExperiment",
            date="2024-01-01",
            workflow="GenerateFASTQ",
            extra_metadata=CaseInsensitiveDict({"Application": "Test"}),
        )
        builder.set_header(header)

        # Set reads
        reads = IlluminaReads(read_lengths=[150, 150])
        builder.set_reads(reads)

        # Set settings
        settings = IlluminaSettings(
            data=CaseInsensitiveDict({"Setting1": "Value1"}), extra_metadata=CaseInsensitiveDict()
        )
        builder.set_settings(settings)

        # Add samples
        samples = [
            IlluminaSample(sample_id="S1", sample_name="Sample1", index="ATCG", sample_project="P1"),
            IlluminaSample(sample_id="S2", sample_name="Sample2", index="GCTA", sample_project="P2"),
            IlluminaSample(sample_id="S3", sample_name="Sample3", index="TGAC", sample_project="P1"),
        ]
        builder.add_samples(samples)

        # Update some components
        builder.update_header_field("experiment_name", "UpdatedExperiment")
        builder.update_reads([100, 100, 50])
        builder.update_settings_field("Setting2", "Value2")
        builder.update_sample("S2", sample_project="UpdatedP2")
        builder.remove_sample("S3")

        sheet = builder.build()

        # Verify final state
        assert sheet.header.experiment_name == "UpdatedExperiment"
        assert sheet.reads is not None
        assert sheet.reads.read_lengths == [100, 100, 50]
        assert sheet.settings is not None
        assert sheet.settings.data["Setting1"] == "Value1"
        assert sheet.settings.data["Setting2"] == "Value2"
        assert len(sheet.data) == 2
        assert sheet.data[0].sample_id == "S1"
        assert sheet.data[1].sample_id == "S2"
        assert sheet.data[1].sample_project == "UpdatedP2"

    def test_builder_method_chaining(self):
        """Test that all builder methods return self for chaining."""
        builder = IlluminaSheetBuilder()

        # Test that all methods return self
        result = (
            builder.set_header(
                IlluminaHeader(
                    iem_file_version="5",
                    experiment_name="Test",
                    date="2024-01-01",
                    workflow="GenerateFASTQ",
                    extra_metadata=CaseInsensitiveDict(),
                )
            )
            .set_reads(IlluminaReads(read_lengths=[150]))
            .set_settings(IlluminaSettings(data=CaseInsensitiveDict({"S": "V"}), extra_metadata=CaseInsensitiveDict()))
            .add_sample(IlluminaSample(sample_id="S1", sample_name="Sample1", index="ATCG"))
            .update_header_field("experiment_name", "Updated")
            .update_reads([100])
            .update_settings_field("S", "Updated")
        )

        assert result is builder

    def test_builder_immutability_of_built_sheet(self):
        """Test that built sheets are independent of builder modifications."""
        builder = IlluminaSheetBuilder()
        sample = IlluminaSample(sample_id="S1", sample_name="Sample1", index="ATCG")
        builder.add_sample(sample)

        # Build first sheet
        sheet1 = builder.build()
        assert len(sheet1.data) == 1

        # Modify builder and build second sheet
        builder.add_sample(IlluminaSample(sample_id="S2", sample_name="Sample2", index="GCTA"))
        sheet2 = builder.build()

        # Verify sheets are independent
        assert len(sheet1.data) == 1
        assert len(sheet2.data) == 2
        assert sheet1.data[0].sample_id == "S1"
        assert sheet2.data[0].sample_id == "S1"
        assert sheet2.data[1].sample_id == "S2"


class TestIlluminaSheetBuilderErrorCases:
    """Test error cases for comprehensive coverage of the builder."""

    def test_remove_sample_not_found_by_object(self):
        """Test removing a sample object that's not in the builder."""
        builder = IlluminaSheetBuilder()
        existing_sample = IlluminaSample(sample_id="Existing", sample_name="Existing", index="AAAA")
        non_existent_sample = IlluminaSample(sample_id="NotFound", sample_name="NotFound", index="TTTT")

        builder.add_sample(existing_sample)

        with pytest.raises(ValueError, match="Sample not found"):
            builder.remove_sample(non_existent_sample)

    def test_remove_sample_not_found_by_id(self):
        """Test removing a sample by ID that doesn't exist."""
        builder = IlluminaSheetBuilder()
        builder.add_sample(IlluminaSample(sample_id="Existing", sample_name="Existing", index="AAAA"))

        with pytest.raises(ValueError, match="Sample with ID 'NotFound' not found"):
            builder.remove_sample("NotFound")

    def test_remove_sample_by_index_out_of_range(self):
        """Test removing a sample by index that's out of range."""
        builder = IlluminaSheetBuilder()
        builder.add_sample(IlluminaSample(sample_id="Existing", sample_name="Existing", index="AAAA"))

        with pytest.raises(IndexError, match="Sample index 10 is out of range"):
            builder.remove_sample(10)

    def test_update_sample_not_found_by_id(self):
        """Test updating a sample by ID that doesn't exist."""
        builder = IlluminaSheetBuilder()
        builder.add_sample(IlluminaSample(sample_id="Existing", sample_name="Existing", index="AAAA"))

        with pytest.raises(ValueError, match="Sample with ID 'NotFound' not found"):
            builder.update_sample("NotFound", sample_name="Updated")

    def test_update_sample_by_index_out_of_range(self):
        """Test updating a sample by index that's out of range."""
        builder = IlluminaSheetBuilder()
        builder.add_sample(IlluminaSample(sample_id="Existing", sample_name="Existing", index="AAAA"))

        with pytest.raises(ValueError, match="Sample index 10 out of range"):
            builder.update_sample(10, sample_name="Updated")

    def test_remove_sample_invalid_type(self):
        """Test removing sample with invalid type parameter."""
        builder = IlluminaSheetBuilder()
        builder.add_sample(IlluminaSample(sample_id="Existing", sample_name="Existing", index="AAAA"))

        with pytest.raises(ValueError, match="Sample must be IlluminaSample, str \\(sample_id\\), or int \\(index\\)"):
            builder.remove_sample(42.5)  # type: ignore[arg-type]  # Testing runtime type validation

    def test_remove_samples_by_project(self):
        """Test removing samples by project."""
        builder = IlluminaSheetBuilder()

        # Add samples with different projects
        builder.add_sample(
            IlluminaSample(sample_id="S1", sample_name="Sample1", index="AAAA", sample_project="ProjectA")
        )
        builder.add_sample(
            IlluminaSample(sample_id="S2", sample_name="Sample2", index="TTTT", sample_project="ProjectB")
        )
        builder.add_sample(
            IlluminaSample(sample_id="S3", sample_name="Sample3", index="GGGG", sample_project="ProjectA")
        )

        # Remove samples by project
        result = builder.remove_samples_by_project("ProjectA")

        # Should remove S1 and S3, leaving S2
        assert len(result._samples) == 1
        assert result._samples[0].sample_id == "S2"
        assert result is builder  # Should return self for chaining

    def test_update_header_field_with_unknown_field(self):
        """Test updating header field with unknown field name."""
        builder = IlluminaSheetBuilder()
        builder.set_header(IlluminaHeader(experiment_name="Test"))

        # Update with an unknown field - should be stored in extra_metadata
        result = builder.update_header_field("UnknownField", "UnknownValue")

        built_sheet = result.build()
        assert built_sheet.header.extra_metadata["UnknownField"] == "UnknownValue"
        assert result is builder  # Should return self for chaining
