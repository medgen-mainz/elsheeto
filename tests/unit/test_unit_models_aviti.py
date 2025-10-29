"""Unit tests for Aviti models."""

import pytest
from pydantic import ValidationError

from elsheeto.models.aviti import (
    AvitiRunValues,
    AvitiSample,
    AvitiSettingEntries,
    AvitiSettingEntry,
    AvitiSettings,
    AvitiSheet,
)


class TestAvitiSample:
    """Test AvitiSample model validation."""

    def test_valid_sample_basic(self):
        """Test creating a valid basic sample."""
        sample = AvitiSample(
            sample_name="Sample1",
            index1="ATGC",
            index2="TCGA",
        )
        assert sample.sample_name == "Sample1"
        assert sample.index1 == "ATGC"
        assert sample.index2 == "TCGA"

    def test_valid_sample_with_empty_index2(self):
        """Test creating a valid sample with empty index2."""
        sample = AvitiSample(
            sample_name="Sample1",
            index1="ATGC",
            index2="",
        )
        assert sample.sample_name == "Sample1"
        assert sample.index1 == "ATGC"
        assert sample.index2 == ""

    def test_valid_sample_composite_indices(self):
        """Test creating a valid sample with composite indices."""
        sample = AvitiSample(
            sample_name="Sample1",
            index1="ATGC+TCGA",
            index2="CCGG+TTAA",
        )
        assert sample.sample_name == "Sample1"
        assert sample.index1 == "ATGC+TCGA"
        assert sample.index2 == "CCGG+TTAA"

    def test_invalid_index1_empty(self):
        """Test that empty index1 raises validation error."""
        with pytest.raises(ValidationError, match="Index1 cannot be empty"):
            AvitiSample(
                sample_name="Sample1",
                index1="",
                index2="TCGA",
            )

    def test_invalid_index1_whitespace_only(self):
        """Test that whitespace-only index1 raises validation error."""
        with pytest.raises(ValidationError, match="Index1 cannot be empty"):
            AvitiSample(
                sample_name="Sample1",
                index1="   ",
                index2="TCGA",
            )

    def test_invalid_index1_empty_part_in_composite(self):
        """Test that empty part in composite index1 raises validation error."""
        with pytest.raises(ValidationError, match="Index parts cannot be empty"):
            AvitiSample(
                sample_name="Sample1",
                index1="ATGC++TCGA",
                index2="CCGG",
            )

    def test_invalid_index1_special_characters(self):
        """Test that invalid characters in index1 raise validation error."""
        with pytest.raises(ValidationError, match="Invalid characters in index"):
            AvitiSample(
                sample_name="Sample1",
                index1="ATGC@INVALID",
                index2="TCGA",
            )

    def test_invalid_index2_empty_part_in_composite(self):
        """Test that empty part in composite index2 raises validation error."""
        with pytest.raises(ValidationError, match="Index parts cannot be empty"):
            AvitiSample(
                sample_name="Sample1",
                index1="ATGC",
                index2="CCGG++TTAA",
            )

    def test_invalid_index2_special_characters(self):
        """Test that invalid characters in index2 raise validation error."""
        with pytest.raises(ValidationError, match="Invalid characters in index"):
            AvitiSample(
                sample_name="Sample1",
                index1="ATGC",
                index2="TCGA!INVALID",
            )

    def test_valid_sample_with_all_fields(self):
        """Test creating a valid sample with all optional fields."""
        sample = AvitiSample(
            sample_name="Sample1",
            index1="ATGC",
            index2="TCGA",
            lane="1",
            project="Project1",
            external_id="EXT123",
            description="Test sample",
            extra_metadata={"Custom": "Value"},
        )
        assert sample.sample_name == "Sample1"
        assert sample.index1 == "ATGC"
        assert sample.index2 == "TCGA"
        assert sample.lane == "1"
        assert sample.project == "Project1"
        assert sample.external_id == "EXT123"
        assert sample.description == "Test sample"
        assert sample.extra_metadata == {"Custom": "Value"}


class TestAvitiRunValues:
    """Test AvitiRunValues model."""

    def test_empty_run_values(self):
        """Test creating empty run values."""
        run_values = AvitiRunValues()
        assert run_values.data == {}
        assert run_values.extra_metadata == {}

    def test_run_values_with_data(self):
        """Test creating run values with data."""
        run_values = AvitiRunValues(
            data={"KeyName": "Value1", "RunId": "Run123"},
            extra_metadata={"Extra": "Data"},
        )
        assert run_values.data == {"KeyName": "Value1", "RunId": "Run123"}
        assert run_values.extra_metadata == {"Extra": "Data"}


class TestAvitiSettings:
    """Test AvitiSettings model."""

    def test_empty_settings(self):
        """Test creating empty settings."""
        settings = AvitiSettings()
        assert settings.data == {}
        assert settings.extra_metadata == {}

    def test_settings_with_data(self):
        """Test creating settings with data."""

        settings = AvitiSettings(
            settings=AvitiSettingEntries(
                entries=[
                    AvitiSettingEntry(name="R1Adapter", value="ATGC"),
                    AvitiSettingEntry(name="R2Adapter", value="CGTA"),
                ]
            ),
            extra_metadata={"Extra": "Data"},
        )
        assert settings.data == {"R1Adapter": "ATGC", "R2Adapter": "CGTA"}
        assert settings.extra_metadata == {"Extra": "Data"}

    def test_settings_lane_specific(self):
        """Test lane-specific settings functionality."""
        settings = AvitiSettings(
            settings=AvitiSettingEntries(
                entries=[
                    AvitiSettingEntry(name="SpikeInAsUnassigned", value="FALSE"),  # No lane
                    AvitiSettingEntry(name="R1FastQMask", value="R1:Y*N", lane="1+2"),
                    AvitiSettingEntry(name="R2FastQMask", value="R2:Y*N", lane="1+2"),
                    AvitiSettingEntry(name="I1Fastq", value="FALSE", lane="1"),
                    AvitiSettingEntry(name="I2Fastq", value="FALSE", lane="2"),
                ]
            )
        )

        # Test backward compatibility
        expected_data = {
            "SpikeInAsUnassigned": "FALSE",
            "R1FastQMask": "R1:Y*N",
            "R2FastQMask": "R2:Y*N",
            "I1Fastq": "FALSE",  # First occurrence wins
            "I2Fastq": "FALSE",
        }
        assert settings.data == expected_data

        # Test lane-specific functionality
        assert settings.get_all_lanes() == {"1+2", "1", "2"}

        # Test settings by lane
        no_lane_settings = settings.get_settings_by_lane(None)
        assert no_lane_settings == {"SpikeInAsUnassigned": "FALSE"}

        lane_12_settings = settings.get_settings_by_lane("1+2")
        assert lane_12_settings == {"R1FastQMask": "R1:Y*N", "R2FastQMask": "R2:Y*N"}

        lane_1_settings = settings.get_settings_by_lane("1")
        assert lane_1_settings == {"I1Fastq": "FALSE"}

        lane_2_settings = settings.get_settings_by_lane("2")
        assert lane_2_settings == {"I2Fastq": "FALSE"}


class TestAvitiSettingEntries:
    """Test AvitiSettingEntries model and its convenience methods."""

    def test_get_all_by_key(self):
        """Test get_all_by_key method."""
        entries = AvitiSettingEntries(
            entries=[
                AvitiSettingEntry(name="R1Adapter", value="ATGC"),
                AvitiSettingEntry(name="R1Adapter", value="GGGG", lane="1"),
                AvitiSettingEntry(name="R2Adapter", value="CGTA"),
            ]
        )

        # Get all R1Adapter entries
        r1_entries = entries.get_all_by_key("R1Adapter")
        assert len(r1_entries) == 2
        assert r1_entries[0].value == "ATGC"
        assert r1_entries[0].lane is None
        assert r1_entries[1].value == "GGGG"
        assert r1_entries[1].lane == "1"

        # Get R2Adapter entries
        r2_entries = entries.get_all_by_key("R2Adapter")
        assert len(r2_entries) == 1
        assert r2_entries[0].value == "CGTA"

        # Get non-existent key
        non_existent = entries.get_all_by_key("NonExistent")
        assert len(non_existent) == 0

    def test_get_by_key_success(self):
        """Test get_by_key method with exactly one match."""
        entries = AvitiSettingEntries(
            entries=[
                AvitiSettingEntry(name="R1Adapter", value="ATGC"),
                AvitiSettingEntry(name="R2Adapter", value="CGTA"),
            ]
        )

        entry = entries.get_by_key("R1Adapter")
        assert entry.value == "ATGC"
        assert entry.lane is None

    def test_get_by_key_not_found(self):
        """Test get_by_key method with no matches."""
        entries = AvitiSettingEntries(entries=[AvitiSettingEntry(name="R1Adapter", value="ATGC")])

        with pytest.raises(ValueError, match="No setting found with key: NonExistent"):
            entries.get_by_key("NonExistent")

    def test_get_by_key_multiple_found(self):
        """Test get_by_key method with multiple matches."""
        entries = AvitiSettingEntries(
            entries=[
                AvitiSettingEntry(name="R1Adapter", value="ATGC"),
                AvitiSettingEntry(name="R1Adapter", value="GGGG", lane="1"),
            ]
        )

        with pytest.raises(ValueError, match="Multiple settings found with key: R1Adapter \\(found 2\\)"):
            entries.get_by_key("R1Adapter")

    def test_get_by_key_and_lane_success(self):
        """Test get_by_key_and_lane method with exact match."""
        entries = AvitiSettingEntries(
            entries=[
                AvitiSettingEntry(name="R1Adapter", value="ATGC"),
                AvitiSettingEntry(name="R1Adapter", value="GGGG", lane="1"),
                AvitiSettingEntry(name="R1Adapter", value="TTTT", lane="2"),
            ]
        )

        # Get by key and no lane
        entry = entries.get_by_key_and_lane("R1Adapter", None)
        assert entry.value == "ATGC"
        assert entry.lane is None

        # Get by key and specific lane
        entry = entries.get_by_key_and_lane("R1Adapter", "1")
        assert entry.value == "GGGG"
        assert entry.lane == "1"

        entry = entries.get_by_key_and_lane("R1Adapter", "2")
        assert entry.value == "TTTT"
        assert entry.lane == "2"

    def test_get_by_key_and_lane_not_found(self):
        """Test get_by_key_and_lane method with no matches."""
        entries = AvitiSettingEntries(entries=[AvitiSettingEntry(name="R1Adapter", value="ATGC", lane="1")])

        with pytest.raises(ValueError, match="No setting found with key: R1Adapter and lane: None"):
            entries.get_by_key_and_lane("R1Adapter", None)

        with pytest.raises(ValueError, match="No setting found with key: NonExistent and lane: '1'"):
            entries.get_by_key_and_lane("NonExistent", "1")

    def test_get_by_key_and_lane_multiple_found(self):
        """Test get_by_key_and_lane method with multiple matches (should not happen in practice)."""
        # This would be an invalid state, but test the error handling
        entries = AvitiSettingEntries(
            entries=[
                AvitiSettingEntry(name="R1Adapter", value="ATGC", lane="1"),
                AvitiSettingEntry(name="R1Adapter", value="GGGG", lane="1"),  # Duplicate key+lane
            ]
        )

        with pytest.raises(ValueError, match="Multiple settings found with key: R1Adapter and lane: '1' \\(found 2\\)"):
            entries.get_by_key_and_lane("R1Adapter", "1")


class TestAvitiSheet:
    """Test AvitiSheet model."""

    def test_minimal_aviti_sheet(self):
        """Test creating minimal Aviti sheet."""
        sample = AvitiSample(sample_name="Sample1", index1="ATGC", index2="TCGA")
        sheet = AvitiSheet(samples=[sample])

        assert sheet.run_values is None
        assert sheet.settings is None
        assert len(sheet.samples) == 1
        assert sheet.samples[0].sample_name == "Sample1"

    def test_complete_aviti_sheet(self):
        """Test creating complete Aviti sheet."""
        sample = AvitiSample(sample_name="Sample1", index1="ATGC", index2="TCGA")
        run_values = AvitiRunValues(data={"RunId": "Run123"})
        settings = AvitiSettings(
            settings=AvitiSettingEntries(entries=[AvitiSettingEntry(name="R1Adapter", value="ATGC")])
        )

        sheet = AvitiSheet(
            run_values=run_values,
            settings=settings,
            samples=[sample],
        )

        assert sheet.run_values is not None
        assert sheet.run_values.data == {"RunId": "Run123"}
        assert sheet.settings is not None
        assert sheet.settings.data == {"R1Adapter": "ATGC"}
        assert len(sheet.samples) == 1
        assert sheet.samples[0].sample_name == "Sample1"
