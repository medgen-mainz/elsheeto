"""Unit tests for Aviti models."""

import pytest
from pydantic import ValidationError

from elsheeto.models.aviti import AvitiRunValues, AvitiSample, AvitiSettings, AvitiSheet


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
            data={"R1Adapter": "ATGC", "R2Adapter": "CGTA"},
            extra_metadata={"Extra": "Data"},
        )
        assert settings.data == {"R1Adapter": "ATGC", "R2Adapter": "CGTA"}
        assert settings.extra_metadata == {"Extra": "Data"}


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
        settings = AvitiSettings(data={"R1Adapter": "ATGC"})

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
