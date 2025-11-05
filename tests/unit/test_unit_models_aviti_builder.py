"""Tests for AvitiSheetBuilder functionality."""

import pytest

from elsheeto.models.aviti import (
    AvitiRunValues,
    AvitiSample,
    AvitiSettingEntries,
    AvitiSettingEntry,
    AvitiSettings,
    AvitiSheet,
    AvitiSheetBuilder,
)
from elsheeto.models.utils import CaseInsensitiveDict


class TestAvitiSheetBuilder:
    """Test cases for AvitiSheetBuilder."""

    def test_empty_builder_initialization(self):
        """Test creating an empty builder."""
        builder = AvitiSheetBuilder()
        sheet = builder.build()

        assert sheet.run_values is None
        assert sheet.settings is None
        assert sheet.samples == []

    def test_from_sheet_initialization(self):
        """Test creating a builder from an existing sheet."""
        # Create a sample sheet
        sample = AvitiSample(sample_name="Test", index1="ATCG")
        run_values = AvitiRunValues(data=CaseInsensitiveDict({"Key": "Value"}))
        settings_entry = AvitiSettingEntry(name="Setting", value="Value")
        settings = AvitiSettings(settings=AvitiSettingEntries(entries=[settings_entry]))

        original_sheet = AvitiSheet(run_values=run_values, settings=settings, samples=[sample])

        # Create builder from sheet
        builder = AvitiSheetBuilder.from_sheet(original_sheet)
        rebuilt_sheet = builder.build()

        assert len(rebuilt_sheet.samples) == 1
        assert rebuilt_sheet.samples[0].sample_name == "Test"
        assert rebuilt_sheet.run_values is not None
        assert rebuilt_sheet.run_values.data["Key"] == "Value"
        assert rebuilt_sheet.settings is not None
        assert len(rebuilt_sheet.settings.settings.entries) == 1

    def test_add_sample(self):
        """Test adding a single sample."""
        builder = AvitiSheetBuilder()
        sample = AvitiSample(sample_name="Test1", index1="ATCG")

        sheet = builder.add_sample(sample).build()

        assert len(sheet.samples) == 1
        assert sheet.samples[0].sample_name == "Test1"

    def test_add_multiple_samples(self):
        """Test adding multiple samples."""
        builder = AvitiSheetBuilder()
        samples = [AvitiSample(sample_name="Test1", index1="ATCG"), AvitiSample(sample_name="Test2", index1="GCTA")]

        sheet = builder.add_samples(samples).build()

        assert len(sheet.samples) == 2
        assert sheet.samples[0].sample_name == "Test1"
        assert sheet.samples[1].sample_name == "Test2"

    def test_remove_sample(self):
        """Test removing a specific sample object."""
        sample1 = AvitiSample(sample_name="Test1", index1="ATCG")
        sample2 = AvitiSample(sample_name="Test2", index1="GCTA")

        builder = AvitiSheetBuilder()
        sheet = builder.add_sample(sample1).add_sample(sample2).remove_sample(sample1).build()

        assert len(sheet.samples) == 1
        assert sheet.samples[0].sample_name == "Test2"

    def test_remove_sample_not_found(self):
        """Test removing a sample that doesn't exist."""
        builder = AvitiSheetBuilder()
        sample = AvitiSample(sample_name="Test", index1="ATCG")

        with pytest.raises(ValueError, match="Sample not found"):
            builder.remove_sample(sample)

    def test_remove_sample_by_name(self):
        """Test removing a sample by name."""
        samples = [AvitiSample(sample_name="Test1", index1="ATCG"), AvitiSample(sample_name="Test2", index1="GCTA")]

        builder = AvitiSheetBuilder()
        sheet = builder.add_samples(samples).remove_sample_by_name("Test1").build()

        assert len(sheet.samples) == 1
        assert sheet.samples[0].sample_name == "Test2"

    def test_remove_sample_by_name_not_found(self):
        """Test removing a sample by name that doesn't exist."""
        builder = AvitiSheetBuilder()

        with pytest.raises(ValueError, match="No sample found with name: NonExistent"):
            builder.remove_sample_by_name("NonExistent")

    def test_remove_samples_by_project(self):
        """Test removing samples by project."""
        samples = [
            AvitiSample(sample_name="Test1", index1="ATCG", project="ProjectA"),
            AvitiSample(sample_name="Test2", index1="GCTA", project="ProjectB"),
            AvitiSample(sample_name="Test3", index1="TGCA", project="ProjectA"),
        ]

        builder = AvitiSheetBuilder()
        sheet = builder.add_samples(samples).remove_samples_by_project("ProjectA").build()

        assert len(sheet.samples) == 1
        assert sheet.samples[0].sample_name == "Test2"
        assert sheet.samples[0].project == "ProjectB"

    def test_update_sample_by_name(self):
        """Test updating a sample by name."""
        sample = AvitiSample(sample_name="Test", index1="ATCG", project="OldProject")

        builder = AvitiSheetBuilder()
        sheet = builder.add_sample(sample).update_sample_by_name("Test", project="NewProject", lane="1").build()

        assert len(sheet.samples) == 1
        updated_sample = sheet.samples[0]
        assert updated_sample.sample_name == "Test"
        assert updated_sample.project == "NewProject"
        assert updated_sample.lane == "1"
        assert updated_sample.index1 == "ATCG"  # Unchanged

    def test_update_sample_by_name_not_found(self):
        """Test updating a sample by name that doesn't exist."""
        builder = AvitiSheetBuilder()

        with pytest.raises(ValueError, match="No sample found with name: NonExistent"):
            builder.update_sample_by_name("NonExistent", project="Test")

    def test_clear_samples(self):
        """Test clearing all samples."""
        samples = [AvitiSample(sample_name="Test1", index1="ATCG"), AvitiSample(sample_name="Test2", index1="GCTA")]

        builder = AvitiSheetBuilder()
        sheet = builder.add_samples(samples).clear_samples().build()

        assert sheet.samples == []

    def test_add_run_value(self):
        """Test adding a run value."""
        builder = AvitiSheetBuilder()
        sheet = builder.add_run_value("Experiment", "Test123").build()

        assert sheet.run_values is not None
        assert sheet.run_values.data["Experiment"] == "Test123"

    def test_add_run_values(self):
        """Test adding multiple run values."""
        builder = AvitiSheetBuilder()
        values = {"Experiment": "Test123", "Date": "2024-01-01"}

        sheet = builder.add_run_values(values).build()

        assert sheet.run_values is not None
        assert sheet.run_values.data["Experiment"] == "Test123"
        assert sheet.run_values.data["Date"] == "2024-01-01"

    def test_remove_run_value(self):
        """Test removing a run value."""
        builder = AvitiSheetBuilder()
        sheet = builder.add_run_value("Key1", "Value1").add_run_value("Key2", "Value2").remove_run_value("Key1").build()

        assert sheet.run_values is not None
        assert "Key1" not in sheet.run_values.data
        assert sheet.run_values.data["Key2"] == "Value2"

    def test_remove_run_value_not_found(self):
        """Test removing a run value that doesn't exist."""
        builder = AvitiSheetBuilder()

        with pytest.raises(KeyError):
            builder.remove_run_value("NonExistent")

    def test_clear_run_values(self):
        """Test clearing all run values."""
        builder = AvitiSheetBuilder()
        sheet = builder.add_run_value("Key1", "Value1").add_run_value("Key2", "Value2").clear_run_values().build()

        assert sheet.run_values is None

    def test_add_setting(self):
        """Test adding a setting."""
        builder = AvitiSheetBuilder()
        sheet = builder.add_setting("ReadLength", "150", "1+2").build()

        assert sheet.settings is not None
        assert len(sheet.settings.settings.entries) == 1
        entry = sheet.settings.settings.entries[0]
        assert entry.name == "ReadLength"
        assert entry.value == "150"
        assert entry.lane == "1+2"

    def test_add_settings(self):
        """Test adding multiple settings."""
        entries = [
            AvitiSettingEntry(name="Setting1", value="Value1"),
            AvitiSettingEntry(name="Setting2", value="Value2", lane="1"),
        ]

        builder = AvitiSheetBuilder()
        sheet = builder.add_settings(entries).build()

        assert sheet.settings is not None
        assert len(sheet.settings.settings.entries) == 2

    def test_remove_settings_by_name(self):
        """Test removing settings by name."""
        builder = AvitiSheetBuilder()
        sheet = (
            builder.add_setting("Setting1", "Value1")
            .add_setting("Setting2", "Value2")
            .add_setting("Setting1", "Value3", "1")  # Same name, different lane
            .remove_settings_by_name("Setting1")
            .build()
        )

        assert sheet.settings is not None
        assert len(sheet.settings.settings.entries) == 1
        assert sheet.settings.settings.entries[0].name == "Setting2"

    def test_remove_settings_by_name_and_lane(self):
        """Test removing settings by name and lane."""
        builder = AvitiSheetBuilder()
        sheet = (
            builder.add_setting("Setting1", "Value1")
            .add_setting("Setting1", "Value2", "1")
            .add_setting("Setting1", "Value3", "2")
            .remove_settings_by_name_and_lane("Setting1", "1")
            .build()
        )

        assert sheet.settings is not None
        assert len(sheet.settings.settings.entries) == 2
        # Should have entries with no lane and lane "2"
        lanes = [entry.lane for entry in sheet.settings.settings.entries]
        assert None in lanes
        assert "2" in lanes
        assert "1" not in lanes

    def test_clear_settings(self):
        """Test clearing all settings."""
        builder = AvitiSheetBuilder()
        sheet = builder.add_setting("Setting1", "Value1").add_setting("Setting2", "Value2").clear_settings().build()

        assert sheet.settings is None

    def test_method_chaining(self):
        """Test that all methods support method chaining."""
        builder = AvitiSheetBuilder()

        # Test chaining multiple operations
        sheet = (
            builder.add_sample(AvitiSample(sample_name="Test1", index1="ATCG"))
            .add_sample(AvitiSample(sample_name="Test2", index1="GCTA"))
            .add_run_value("Experiment", "Test")
            .add_setting("ReadLength", "150")
            .build()
        )

        assert len(sheet.samples) == 2
        assert sheet.run_values is not None
        assert sheet.settings is not None

    def test_builder_reuse(self):
        """Test that builders can be reused and don't interfere with each other."""
        builder = AvitiSheetBuilder()
        builder.add_sample(AvitiSample(sample_name="Test1", index1="ATCG"))

        # Build first sheet
        sheet1 = builder.build()

        # Modify builder and build second sheet
        builder.add_sample(AvitiSample(sample_name="Test2", index1="GCTA"))
        sheet2 = builder.build()

        # First sheet should be unchanged
        assert len(sheet1.samples) == 1
        assert sheet1.samples[0].sample_name == "Test1"

        # Second sheet should have both samples
        assert len(sheet2.samples) == 2
        assert sheet2.samples[0].sample_name == "Test1"
        assert sheet2.samples[1].sample_name == "Test2"
