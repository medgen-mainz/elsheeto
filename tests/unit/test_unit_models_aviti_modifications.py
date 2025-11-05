"""Tests for AvitiSheet fluent modification methods."""

import pytest

from elsheeto.models.aviti import (
    AvitiRunValues,
    AvitiSample,
    AvitiSettingEntries,
    AvitiSettingEntry,
    AvitiSettings,
    AvitiSheet,
)
from elsheeto.models.utils import CaseInsensitiveDict


class TestAvitiSheetModifications:
    """Test cases for AvitiSheet fluent modification methods."""

    @pytest.fixture
    def basic_sheet(self):
        """Create a basic sheet for testing."""
        samples = [
            AvitiSample(sample_name="Sample1", index1="ATCG", project="ProjectA"),
            AvitiSample(sample_name="Sample2", index1="GCTA", project="ProjectB"),
        ]

        run_values = AvitiRunValues(data=CaseInsensitiveDict({"Experiment": "Test123", "Date": "2024-01-01"}))

        settings_entries = [
            AvitiSettingEntry(name="ReadLength", value="150"),
            AvitiSettingEntry(name="Cycles", value="300", lane="1+2"),
        ]
        settings = AvitiSettings(settings=AvitiSettingEntries(entries=settings_entries))

        return AvitiSheet(run_values=run_values, settings=settings, samples=samples)

    def test_with_sample_added(self, basic_sheet):
        """Test adding a sample with fluent API."""
        new_sample = AvitiSample(sample_name="Sample3", index1="TGCA", project="ProjectC")

        modified_sheet = basic_sheet.with_sample_added(new_sample)

        # Original sheet unchanged
        assert len(basic_sheet.samples) == 2

        # Modified sheet has new sample
        assert len(modified_sheet.samples) == 3
        assert modified_sheet.samples[2].sample_name == "Sample3"
        assert modified_sheet.samples[2].project == "ProjectC"

        # Other data preserved
        assert modified_sheet.run_values is not None
        assert modified_sheet.settings is not None

    def test_with_sample_removed(self, basic_sheet):
        """Test removing a sample by name."""
        modified_sheet = basic_sheet.with_sample_removed("Sample1")

        # Original sheet unchanged
        assert len(basic_sheet.samples) == 2

        # Modified sheet has sample removed
        assert len(modified_sheet.samples) == 1
        assert modified_sheet.samples[0].sample_name == "Sample2"

    def test_with_sample_removed_not_found(self, basic_sheet):
        """Test removing a sample that doesn't exist."""
        with pytest.raises(ValueError, match="No sample found with name: NonExistent"):
            basic_sheet.with_sample_removed("NonExistent")

    def test_with_sample_modified(self, basic_sheet):
        """Test modifying a sample by name."""
        modified_sheet = basic_sheet.with_sample_modified(
            "Sample1", project="NewProject", lane="1", description="Modified sample"
        )

        # Original sheet unchanged
        original_sample = basic_sheet.samples[0]
        assert original_sample.project == "ProjectA"
        assert original_sample.lane is None
        assert original_sample.description is None

        # Modified sheet has updated sample
        modified_sample = modified_sheet.samples[0]
        assert modified_sample.sample_name == "Sample1"  # Unchanged
        assert modified_sample.index1 == "ATCG"  # Unchanged
        assert modified_sample.project == "NewProject"  # Changed
        assert modified_sample.lane == "1"  # Changed
        assert modified_sample.description == "Modified sample"  # Changed

        # Other samples unchanged
        assert modified_sheet.samples[1].sample_name == "Sample2"
        assert modified_sheet.samples[1].project == "ProjectB"

    def test_with_sample_modified_not_found(self, basic_sheet):
        """Test modifying a sample that doesn't exist."""
        with pytest.raises(ValueError, match="No sample found with name: NonExistent"):
            basic_sheet.with_sample_modified("NonExistent", project="Test")

    def test_with_samples_filtered(self, basic_sheet):
        """Test filtering samples with a predicate."""
        # Keep only samples from ProjectA
        modified_sheet = basic_sheet.with_samples_filtered(lambda s: s.project == "ProjectA")

        # Original sheet unchanged
        assert len(basic_sheet.samples) == 2

        # Modified sheet has filtered samples
        assert len(modified_sheet.samples) == 1
        assert modified_sheet.samples[0].sample_name == "Sample1"
        assert modified_sheet.samples[0].project == "ProjectA"

    def test_with_samples_filtered_empty_result(self, basic_sheet):
        """Test filtering that results in no samples."""
        # Filter that matches no samples
        modified_sheet = basic_sheet.with_samples_filtered(lambda s: s.project == "NonExistentProject")

        assert len(modified_sheet.samples) == 0

    def test_with_run_value_added_to_existing(self, basic_sheet):
        """Test adding a run value to existing run values."""
        modified_sheet = basic_sheet.with_run_value_added("NewKey", "NewValue")

        # Original sheet unchanged
        assert "NewKey" not in basic_sheet.run_values.data

        # Modified sheet has new run value
        assert modified_sheet.run_values is not None
        assert modified_sheet.run_values.data["NewKey"] == "NewValue"
        assert modified_sheet.run_values.data["Experiment"] == "Test123"  # Existing preserved

    def test_with_run_value_added_to_empty(self):
        """Test adding a run value to a sheet with no run values."""
        sheet = AvitiSheet(samples=[])

        modified_sheet = sheet.with_run_value_added("FirstKey", "FirstValue")

        assert sheet.run_values is None  # Original unchanged
        assert modified_sheet.run_values is not None
        assert modified_sheet.run_values.data["FirstKey"] == "FirstValue"

    def test_with_run_value_added_update_existing(self, basic_sheet):
        """Test updating an existing run value."""
        modified_sheet = basic_sheet.with_run_value_added("Experiment", "UpdatedTest")

        # Original sheet unchanged
        assert basic_sheet.run_values.data["Experiment"] == "Test123"

        # Modified sheet has updated value
        assert modified_sheet.run_values.data["Experiment"] == "UpdatedTest"
        assert modified_sheet.run_values.data["Date"] == "2024-01-01"  # Other values preserved

    def test_with_run_values_updated(self, basic_sheet):
        """Test updating multiple run values."""
        updates = {"Experiment": "UpdatedTest", "NewKey": "NewValue", "Date": "2024-12-31"}

        modified_sheet = basic_sheet.with_run_values_updated(updates)

        # Original sheet unchanged
        assert basic_sheet.run_values.data["Experiment"] == "Test123"
        assert basic_sheet.run_values.data["Date"] == "2024-01-01"
        assert "NewKey" not in basic_sheet.run_values.data

        # Modified sheet has all updates
        assert modified_sheet.run_values.data["Experiment"] == "UpdatedTest"
        assert modified_sheet.run_values.data["Date"] == "2024-12-31"
        assert modified_sheet.run_values.data["NewKey"] == "NewValue"

    def test_with_run_values_updated_empty_sheet(self):
        """Test updating run values on a sheet with no run values."""
        sheet = AvitiSheet(samples=[])
        updates = {"Key1": "Value1", "Key2": "Value2"}

        modified_sheet = sheet.with_run_values_updated(updates)

        assert sheet.run_values is None  # Original unchanged
        assert modified_sheet.run_values is not None
        assert modified_sheet.run_values.data["Key1"] == "Value1"
        assert modified_sheet.run_values.data["Key2"] == "Value2"

    def test_with_setting_added_to_existing(self, basic_sheet):
        """Test adding a setting to existing settings."""
        modified_sheet = basic_sheet.with_setting_added("NewSetting", "NewValue", "1")

        # Original sheet unchanged
        assert len(basic_sheet.settings.settings.entries) == 2

        # Modified sheet has new setting
        assert len(modified_sheet.settings.settings.entries) == 3

        # Find the new setting
        new_setting = None
        for entry in modified_sheet.settings.settings.entries:
            if entry.name == "NewSetting":
                new_setting = entry
                break

        assert new_setting is not None
        assert new_setting.value == "NewValue"
        assert new_setting.lane == "1"

    def test_with_setting_added_to_empty(self):
        """Test adding a setting to a sheet with no settings."""
        sheet = AvitiSheet(samples=[])

        modified_sheet = sheet.with_setting_added("FirstSetting", "FirstValue")

        assert sheet.settings is None  # Original unchanged
        assert modified_sheet.settings is not None
        assert len(modified_sheet.settings.settings.entries) == 1

        entry = modified_sheet.settings.settings.entries[0]
        assert entry.name == "FirstSetting"
        assert entry.value == "FirstValue"
        assert entry.lane is None

    def test_immutability_preservation(self, basic_sheet):
        """Test that all modification methods preserve immutability."""
        new_sample = AvitiSample(sample_name="NewSample", index1="AAAA")

        # Apply multiple modifications
        modified_sheet = (
            basic_sheet.with_sample_added(new_sample)
            .with_sample_modified("Sample1", project="ModifiedProject")
            .with_run_value_added("NewRun", "NewRunValue")
            .with_setting_added("NewSetting", "NewSettingValue")
        )

        # Original sheet completely unchanged
        assert len(basic_sheet.samples) == 2
        assert basic_sheet.samples[0].project == "ProjectA"
        assert basic_sheet.run_values.data["Experiment"] == "Test123"
        assert len(basic_sheet.settings.settings.entries) == 2

        # Modified sheet has all changes
        assert len(modified_sheet.samples) == 3
        assert modified_sheet.samples[0].project == "ModifiedProject"
        assert modified_sheet.run_values.data["NewRun"] == "NewRunValue"
        assert len(modified_sheet.settings.settings.entries) == 3

    def test_method_chaining(self, basic_sheet):
        """Test that fluent methods can be chained together."""
        new_sample = AvitiSample(sample_name="ChainedSample", index1="TTTT")

        # Chain multiple operations
        modified_sheet = (
            basic_sheet.with_sample_added(new_sample)
            .with_sample_removed("Sample2")
            .with_sample_modified("Sample1", lane="2")
            .with_run_value_added("ChainedRun", "ChainedValue")
            .with_setting_added("ChainedSetting", "ChainedSettingValue")
        )

        # Verify all operations were applied
        assert len(modified_sheet.samples) == 2  # Added 1, removed 1
        assert modified_sheet.samples[0].lane == "2"  # Modified Sample1
        assert modified_sheet.samples[1].sample_name == "ChainedSample"  # Added sample
        assert modified_sheet.run_values.data["ChainedRun"] == "ChainedValue"
        assert any(entry.name == "ChainedSetting" for entry in modified_sheet.settings.settings.entries)
