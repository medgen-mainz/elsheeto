"""Tests for IlluminaSampleSheet fluent modification methods."""

import pytest

from elsheeto.models.illumina_v1 import (
    IlluminaHeader,
    IlluminaReads,
    IlluminaSample,
    IlluminaSampleSheet,
    IlluminaSettings,
)
from elsheeto.models.utils import CaseInsensitiveDict


@pytest.fixture
def basic_sheet():
    """Create a basic sheet for testing."""
    samples = [
        IlluminaSample(
            sample_id="Sample1",
            sample_name="Sample1",
            index="ATCG",
            index2="GCTA",
            sample_project="ProjectA",
        ),
        IlluminaSample(
            sample_id="Sample2",
            sample_name="Sample2",
            index="GCTA",
            index2="ATCG",
            sample_project="ProjectB",
        ),
    ]

    header = IlluminaHeader(
        iem_file_version="5",
        experiment_name="TestExperiment",
        date="2024-01-01",
        workflow="GenerateFASTQ",
        application="Test App",
        extra_metadata=CaseInsensitiveDict(),
    )

    reads = IlluminaReads(read_lengths=[150, 150])
    settings = IlluminaSettings(data=CaseInsensitiveDict({"Setting1": "Value1"}), extra_metadata=CaseInsensitiveDict())

    return IlluminaSampleSheet(header=header, reads=reads, settings=settings, data=samples)


class TestIlluminaSampleSheetModifications:
    """Test cases for IlluminaSampleSheet fluent modification methods."""

    def test_with_sample_added(self, basic_sheet):
        """Test adding a sample with fluent API."""
        new_sample = IlluminaSample(
            sample_id="Sample3",
            sample_name="Sample3",
            index="TGCA",
            index2="ACGT",
            sample_project="ProjectC",
        )

        modified_sheet = basic_sheet.with_sample_added(new_sample)

        # Original sheet unchanged
        assert len(basic_sheet.data) == 2

        # Modified sheet has new sample
        assert len(modified_sheet.data) == 3
        assert modified_sheet.data[2].sample_id == "Sample3"
        assert modified_sheet.data[2].sample_project == "ProjectC"

        # Other data preserved
        assert modified_sheet.header.experiment_name == "TestExperiment"
        assert modified_sheet.reads.read_lengths == [150, 150]

    def test_with_sample_added_at_position(self, basic_sheet):
        """Test adding a sample at a specific position."""
        new_sample = IlluminaSample(
            sample_id="Sample3",
            sample_name="Sample3",
            index="TGCA",
            index2="ACGT",
            sample_project="ProjectC",
        )

        modified_sheet = basic_sheet.with_sample_added(new_sample, position=1)

        # Original sheet unchanged
        assert len(basic_sheet.data) == 2

        # Modified sheet has new sample at position 1
        assert len(modified_sheet.data) == 3
        assert modified_sheet.data[1].sample_id == "Sample3"
        assert modified_sheet.data[0].sample_id == "Sample1"
        assert modified_sheet.data[2].sample_id == "Sample2"

    def test_with_sample_removed_by_id(self, basic_sheet):
        """Test removing a sample by ID."""
        modified_sheet = basic_sheet.with_sample_removed("Sample1")

        # Original sheet unchanged
        assert len(basic_sheet.data) == 2

        # Modified sheet has sample removed
        assert len(modified_sheet.data) == 1
        assert modified_sheet.data[0].sample_id == "Sample2"

        # Other data preserved
        assert modified_sheet.header.experiment_name == "TestExperiment"

    def test_with_sample_removed_by_index(self, basic_sheet):
        """Test removing a sample by index."""
        modified_sheet = basic_sheet.with_sample_removed(0)

        # Original sheet unchanged
        assert len(basic_sheet.data) == 2

        # Modified sheet has sample removed
        assert len(modified_sheet.data) == 1
        assert modified_sheet.data[0].sample_id == "Sample2"

    def test_with_sample_removed_nonexistent_id(self, basic_sheet):
        """Test removing a non-existent sample by ID."""
        with pytest.raises(ValueError, match="Sample with ID 'NonExistent' not found"):
            basic_sheet.with_sample_removed("NonExistent")

    def test_with_sample_removed_invalid_index(self, basic_sheet):
        """Test removing a sample with invalid index."""
        with pytest.raises(IndexError, match="Sample index 5 is out of range"):
            basic_sheet.with_sample_removed(5)

    def test_with_sample_modified_by_id(self, basic_sheet):
        """Test modifying a sample by ID."""
        modifications = {"sample_project": "UpdatedProject", "description": "Updated description"}

        modified_sheet = basic_sheet.with_sample_modified("Sample1", **modifications)

        # Original sheet unchanged
        assert basic_sheet.data[0].sample_project == "ProjectA"
        assert basic_sheet.data[0].description is None

        # Modified sheet has updated sample
        assert modified_sheet.data[0].sample_project == "UpdatedProject"
        assert modified_sheet.data[0].description == "Updated description"
        assert modified_sheet.data[0].sample_id == "Sample1"  # ID preserved
        assert modified_sheet.data[1].sample_project == "ProjectB"  # Other samples unchanged

    def test_with_sample_modified_by_index(self, basic_sheet):
        """Test modifying a sample by index."""
        modifications = {"sample_name": "UpdatedName", "index": "AAAA"}

        modified_sheet = basic_sheet.with_sample_modified(1, **modifications)

        # Original sheet unchanged
        assert basic_sheet.data[1].sample_name == "Sample2"
        assert basic_sheet.data[1].index == "GCTA"

        # Modified sheet has updated sample
        assert modified_sheet.data[1].sample_name == "UpdatedName"
        assert modified_sheet.data[1].index == "AAAA"
        assert modified_sheet.data[1].sample_id == "Sample2"  # ID preserved
        assert modified_sheet.data[0].sample_name == "Sample1"  # Other samples unchanged

    def test_with_sample_modified_nonexistent_id(self, basic_sheet):
        """Test modifying a non-existent sample by ID."""
        with pytest.raises(ValueError, match="Sample with ID 'NonExistent' not found"):
            basic_sheet.with_sample_modified("NonExistent", sample_name="Updated")

    def test_with_sample_modified_invalid_index(self, basic_sheet):
        """Test modifying a sample with invalid index."""
        with pytest.raises(IndexError, match="Sample index 5 is out of range"):
            basic_sheet.with_sample_modified(5, sample_name="Updated")

    def test_with_sample_modified_invalid_field(self, basic_sheet):
        """Test modifying a sample with invalid field."""
        with pytest.raises(ValueError, match="Invalid field 'invalid_field' for IlluminaSample"):
            basic_sheet.with_sample_modified("Sample1", invalid_field="value")

    def test_with_header_field_updated(self, basic_sheet):
        """Test updating a header field."""
        modified_sheet = basic_sheet.with_header_field_updated("experiment_name", "UpdatedExperiment")

        # Original sheet unchanged
        assert basic_sheet.header.experiment_name == "TestExperiment"

        # Modified sheet has updated header
        assert modified_sheet.header.experiment_name == "UpdatedExperiment"
        assert modified_sheet.header.date == "2024-01-01"  # Other fields preserved

        # Other data preserved
        assert len(modified_sheet.data) == 2

    def test_with_header_field_updated_extra_metadata(self, basic_sheet):
        """Test updating a header extra metadata field."""
        modified_sheet = basic_sheet.with_header_field_updated("Application", "Updated App")

        # Original sheet unchanged
        assert basic_sheet.header.application == "Test App"

        # Modified sheet has updated extra metadata
        assert modified_sheet.header.application == "Updated App"

    def test_with_header_field_updated_new_extra_metadata(self, basic_sheet):
        """Test adding a new header extra metadata field."""
        modified_sheet = basic_sheet.with_header_field_updated("NewField", "NewValue")

        # Original sheet unchanged
        assert "NewField" not in basic_sheet.header.extra_metadata

        # Modified sheet has new extra metadata field
        assert modified_sheet.header.extra_metadata["NewField"] == "NewValue"
        assert modified_sheet.header.application == "Test App"  # Existing preserved

    def test_with_header_field_updated_invalid_field(self, basic_sheet):
        """Test updating an invalid header field (goes to extra_metadata)."""
        modified_sheet = basic_sheet.with_header_field_updated("invalid_field", "value")

        # Should be added to extra_metadata
        assert modified_sheet.header.extra_metadata["invalid_field"] == "value"

    def test_with_reads_updated(self, basic_sheet):
        """Test updating read lengths."""
        new_reads = [75, 75, 50]
        modified_sheet = basic_sheet.with_reads_updated(new_reads)

        # Original sheet unchanged
        assert basic_sheet.reads.read_lengths == [150, 150]

        # Modified sheet has updated reads
        assert modified_sheet.reads.read_lengths == [75, 75, 50]

        # Other data preserved
        assert modified_sheet.header.experiment_name == "TestExperiment"
        assert len(modified_sheet.data) == 2

    def test_with_reads_updated_single_read(self, basic_sheet):
        """Test updating to single read."""
        new_reads = [100]
        modified_sheet = basic_sheet.with_reads_updated(new_reads)

        assert modified_sheet.reads.read_lengths == [100]

    def test_with_reads_updated_empty(self, basic_sheet):
        """Test updating to empty reads."""
        modified_sheet = basic_sheet.with_reads_updated([])

        assert modified_sheet.reads.read_lengths == []

    def test_with_settings_field_updated(self, basic_sheet):
        """Test updating a settings field."""
        modified_sheet = basic_sheet.with_settings_field_updated("Setting1", "UpdatedValue")

        # Original sheet unchanged
        assert basic_sheet.settings.data["Setting1"] == "Value1"

        # Modified sheet has updated setting
        assert modified_sheet.settings.data["Setting1"] == "UpdatedValue"

        # Other data preserved
        assert len(modified_sheet.data) == 2

    def test_with_settings_field_updated_new_field(self, basic_sheet):
        """Test adding a new settings field."""
        modified_sheet = basic_sheet.with_settings_field_updated("NewSetting", "NewValue")

        # Original sheet unchanged
        assert "NewSetting" not in basic_sheet.settings.data

        # Modified sheet has new setting
        assert modified_sheet.settings.data["NewSetting"] == "NewValue"
        assert modified_sheet.settings.data["Setting1"] == "Value1"  # Existing preserved

    def test_chaining_modifications(self, basic_sheet):
        """Test chaining multiple modifications."""
        new_sample = IlluminaSample(
            sample_id="Sample3",
            sample_name="Sample3",
            index="AAAA",
            index2="TTTT",
            sample_project="ProjectC",
        )

        modified_sheet = (
            basic_sheet.with_sample_added(new_sample)
            .with_sample_removed("Sample1")
            .with_header_field_updated("experiment_name", "ChainedExperiment")
            .with_reads_updated([100, 100])
            .with_settings_field_updated("Setting1", "ChainedValue")
        )

        # Verify final state
        assert len(modified_sheet.data) == 2
        assert modified_sheet.data[0].sample_id == "Sample2"
        assert modified_sheet.data[1].sample_id == "Sample3"
        assert modified_sheet.header.experiment_name == "ChainedExperiment"
        assert modified_sheet.reads.read_lengths == [100, 100]
        assert modified_sheet.settings.data["Setting1"] == "ChainedValue"

        # Original sheet unchanged
        assert len(basic_sheet.data) == 2
        assert basic_sheet.header.experiment_name == "TestExperiment"
        assert basic_sheet.reads.read_lengths == [150, 150]
        assert basic_sheet.settings.data["Setting1"] == "Value1"

    def test_modification_immutability(self, basic_sheet):
        """Test that modifications don't affect the original sheet."""
        original_samples_count = len(basic_sheet.data)
        original_experiment_name = basic_sheet.header.experiment_name
        original_read_lengths = basic_sheet.reads.read_lengths.copy()
        original_setting_value = basic_sheet.settings.data["Setting1"]

        # Perform multiple modifications
        new_sample = IlluminaSample(sample_id="New", sample_name="New", index="AAAA")
        basic_sheet.with_sample_added(new_sample)
        basic_sheet.with_header_field_updated("experiment_name", "Modified")
        basic_sheet.with_reads_updated([75])
        basic_sheet.with_settings_field_updated("Setting1", "Modified")

        # Verify original sheet is unchanged
        assert len(basic_sheet.data) == original_samples_count
        assert basic_sheet.header.experiment_name == original_experiment_name
        assert basic_sheet.reads.read_lengths == original_read_lengths
        assert basic_sheet.settings.data["Setting1"] == original_setting_value


class TestIlluminaSampleSheetErrorCases:
    """Test error cases for comprehensive coverage."""

    def test_with_settings_field_when_no_settings(self):
        """Test adding settings field when settings section doesn't exist."""
        sheet = IlluminaSampleSheet(
            header=IlluminaHeader(experiment_name="Test"),
            reads=IlluminaReads(read_lengths=[150]),
            settings=None,
            data=[IlluminaSample(sample_id="S1", sample_name="Sample1", index="AAAA")],
        )

        result = sheet.with_settings_field_updated("NewSetting", "NewValue")

        assert result.settings is not None
        assert result.settings.data["NewSetting"] == "NewValue"
