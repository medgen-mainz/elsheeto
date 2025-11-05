"""Aviti sample sheet (aka Sequencing Manifest) specific models.

The Stage 2 results are converted into these models in Stage 3.
"""

from typing import TYPE_CHECKING, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator

from elsheeto.models.utils import CaseInsensitiveDict

if TYPE_CHECKING:
    from elsheeto.writer.base import WriterConfiguration


class AvitiSample(BaseModel):
    """Representation of a single Aviti sample."""

    #: Required value from `SampleName` column.
    sample_name: str
    #: Required value from `Index1` column - can contain composite indices separated by +.
    index1: str
    #: Optional value from `Index2` column - can contain composite indices separated by +.
    index2: str = ""
    #: Optional value from `Lane` column.
    lane: str | None = None
    #: Optional value from `Project` column.
    project: str | None = None
    #: Optional value from `ExternalId` column.
    external_id: str | None = None
    #: Optional value from `Description` column.
    description: str | None = None

    #: Optional extra metadata for unknown fields.
    extra_metadata: CaseInsensitiveDict = Field(default_factory=CaseInsensitiveDict)

    #: Model configuration.
    model_config = ConfigDict(frozen=True)

    @field_validator("index1")
    @classmethod
    def validate_index1(cls, v: str) -> str:
        """Validate index1 sequence.

        Args:
            v: The index sequence(s), potentially composite.

        Returns:
            The validated index sequence.

        Raises:
            ValueError: If index is invalid.
        """
        if not v or not v.strip():
            raise ValueError("Index1 cannot be empty")

        # Split composite indices and validate each part
        parts = v.split("+")
        for part in parts:
            part = part.strip()
            if not part:
                raise ValueError("Index parts cannot be empty")
            # Allow DNA sequences (ATCG) and common index names
            if not all(c in "ATCGNatcgn" or c.isalnum() or c in "_-" for c in part):
                raise ValueError(f"Invalid characters in index: {part}")

        return v

    @field_validator("index2")
    @classmethod
    def validate_index2(cls, v: str) -> str:
        """Validate index2 sequence.

        Args:
            v: The index sequence(s), potentially composite.

        Returns:
            The validated index sequence.

        Raises:
            ValueError: If index is invalid.
        """
        # Index2 can be empty for some Aviti configurations
        if not v or not v.strip():
            return ""

        # Split composite indices and validate each part
        parts = v.split("+")
        for part in parts:
            part = part.strip()
            if not part:
                raise ValueError("Index parts cannot be empty")
            # Allow DNA sequences (ATCG) and common index names
            if not all(c in "ATCGNatcgn" or c.isalnum() or c in "_-" for c in part):
                raise ValueError(f"Invalid characters in index: {part}")

        return v


class AvitiRunValues(BaseModel):
    """Representation of the `RunValues` section of an Aviti sample sheet."""

    #: Key-value pairs from the RunValues section.
    data: CaseInsensitiveDict = Field(default_factory=CaseInsensitiveDict)
    #: Optional extra metadata.
    extra_metadata: CaseInsensitiveDict = Field(default_factory=CaseInsensitiveDict)

    model_config = ConfigDict(frozen=True)


class AvitiSettingEntry(BaseModel):
    """Representation of a single setting entry that may be lane-specific."""

    #: Setting name/key.
    name: str
    #: Setting value.
    value: str
    #: Optional lane specification (e.g., "1+2", "1", "2", etc.).
    lane: str | None = None

    model_config = ConfigDict(frozen=True)


class AvitiSettingEntries(BaseModel):
    """Collection of Aviti setting entries with convenience methods for retrieval."""

    #: List of setting entries (may include lane-specific settings).
    entries: list[AvitiSettingEntry] = Field(default_factory=list)

    model_config = ConfigDict(frozen=True)

    def get_all_by_key(self, key: str) -> list[AvitiSettingEntry]:
        """Get all setting entries with the specified key.

        Args:
            key: Setting name to search for.

        Returns:
            List of all setting entries with the specified key.
        """
        return [entry for entry in self.entries if entry.name.lower() == key.lower()]

    def get_by_key(self, key: str) -> AvitiSettingEntry:
        """Get exactly one setting entry with the specified key.

        Args:
            key: Setting name to search for.

        Returns:
            The single setting entry with the specified key.

        Raises:
            ValueError: If zero or more than one entry found with the key.
        """
        matches = self.get_all_by_key(key)
        if len(matches) == 0:
            raise ValueError(f"No setting found with key: {key}")
        if len(matches) > 1:
            raise ValueError(f"Multiple settings found with key: {key} (found {len(matches)})")
        return matches[0]

    def get_by_key_and_lane(self, key: str, lane: str | None) -> AvitiSettingEntry:
        """Get exactly one setting entry with exact key and lane match.

        Args:
            key: Setting name to search for.
            lane: Lane specification to match exactly (None for no lane).

        Returns:
            The setting entry with exact key and lane match.

        Raises:
            ValueError: If zero or more than one entry found with the key and lane combination.
        """
        matches = [entry for entry in self.entries if entry.name.lower() == key.lower() and entry.lane == lane]
        if len(matches) == 0:
            lane_str = "None" if lane is None else f"'{lane}'"
            raise ValueError(f"No setting found with key: {key} and lane: {lane_str}")
        if len(matches) > 1:
            lane_str = "None" if lane is None else f"'{lane}'"
            raise ValueError(f"Multiple settings found with key: {key} and lane: {lane_str} (found {len(matches)})")
        return matches[0]


class AvitiSettings(BaseModel):
    """Representation of the `Settings` section of an Aviti sample sheet.

    Supports both simple key-value pairs and lane-specific settings with 3-column structure.
    """

    #: Collection of setting entries (may include lane-specific settings).
    settings: AvitiSettingEntries = Field(default_factory=AvitiSettingEntries)
    #: Optional extra metadata.
    extra_metadata: CaseInsensitiveDict = Field(default_factory=CaseInsensitiveDict)

    model_config = ConfigDict(frozen=True)

    @property
    def data(self) -> CaseInsensitiveDict:
        """Get simple key-value pairs for backward compatibility.

        For lane-specific settings, only returns the first occurrence of each setting name.
        """
        result = CaseInsensitiveDict({})
        for setting in self.settings.entries:
            if setting.name not in result:
                result[setting.name] = setting.value
        return result

    def get_settings_by_lane(self, lane: str | None = None) -> CaseInsensitiveDict:
        """Get settings filtered by lane specification.

        Args:
            lane: Lane specification to filter by (e.g., "1", "2", "1+2").
                  If None, returns settings without lane specification.

        Returns:
            Dictionary of setting name to value for the specified lane.
        """
        result = CaseInsensitiveDict({})
        for setting in self.settings.entries:
            if setting.lane == lane:
                result[setting.name] = setting.value
        return result

    def get_all_lanes(self) -> set[str]:
        """Get all unique lane specifications used in settings.

        Returns:
            Set of all lane specifications (excluding None).
        """
        return {setting.lane for setting in self.settings.entries if setting.lane is not None}


class AvitiSheet(BaseModel):
    """Representation of an Aviti sample sheet (officially known as Sequencing Manifest).

    By the documentation, a minimal configuration looks as follows (section header above
    samples does not matter).

    ```
    [RunValues]
    KeyName,Value
    [Settings]
    SettingName, Value
    [Samples]
    SampleName, Index1, Index2,
    ```

    The following is the extended version:

    ```
    [RunValues]
    KeyName,Value
    [Settings]
    SettingName, Value
    [Samples]
    SampleName, Index1, Index2, Lane, Project, ExternalId, Description
    ```
    """

    #: The `RunValues` section.
    run_values: AvitiRunValues | None = None
    #: The `Settings` section.
    settings: AvitiSettings | None = None
    #: The `Samples` section.
    samples: list[AvitiSample]

    model_config = ConfigDict(frozen=True)

    def with_sample_added(self, sample: AvitiSample) -> "AvitiSheet":
        """Create a new sheet with an additional sample.

        Args:
            sample: The sample to add.

        Returns:
            A new AvitiSheet with the sample added.

        Example:
            >>> from elsheeto.models.aviti import AvitiSample, AvitiSheet
            >>> sheet = AvitiSheet(samples=[])
            >>> new_sample = AvitiSample(sample_name="Test", index1="ATCG")
            >>> modified_sheet = sheet.with_sample_added(new_sample)
            >>> len(modified_sheet.samples)
            1
        """
        new_samples = self.samples + [sample]
        return self.model_copy(update={"samples": new_samples})

    def with_sample_removed(self, sample_name: str) -> "AvitiSheet":
        """Create a new sheet with a sample removed by name.

        Args:
            sample_name: The name of the sample to remove.

        Returns:
            A new AvitiSheet with the sample removed.

        Raises:
            ValueError: If no sample with the given name is found.

        Example:
            >>> from elsheeto.models.aviti import AvitiSample, AvitiSheet
            >>> sample = AvitiSample(sample_name="OldSample", index1="ATCG")
            >>> sheet = AvitiSheet(samples=[sample])
            >>> modified_sheet = sheet.with_sample_removed("OldSample")
            >>> len(modified_sheet.samples)
            0
        """
        new_samples = []
        found = False
        for sample in self.samples:
            if sample.sample_name == sample_name:
                found = True
            else:
                new_samples.append(sample)

        if not found:
            raise ValueError(f"No sample found with name: {sample_name}")

        return self.model_copy(update={"samples": new_samples})

    def with_sample_modified(self, sample_name: str, **updates) -> "AvitiSheet":
        """Create a new sheet with a sample modified by name.

        Args:
            sample_name: The name of the sample to modify.
            **updates: Fields to update on the sample.

        Returns:
            A new AvitiSheet with the sample modified.

        Raises:
            ValueError: If no sample with the given name is found.

        Example:
            >>> from elsheeto.models.aviti import AvitiSample, AvitiSheet
            >>> sample = AvitiSample(sample_name="Sample1", index1="ATCG")
            >>> sheet = AvitiSheet(samples=[sample])
            >>> modified_sheet = sheet.with_sample_modified("Sample1", project="NewProject")
            >>> modified_sheet.samples[0].project
            'NewProject'
        """
        new_samples = []
        found = False
        for sample in self.samples:
            if sample.sample_name == sample_name:
                found = True
                new_samples.append(sample.model_copy(update=updates))
            else:
                new_samples.append(sample)

        if not found:
            raise ValueError(f"No sample found with name: {sample_name}")

        return self.model_copy(update={"samples": new_samples})

    def with_samples_filtered(self, predicate) -> "AvitiSheet":
        """Create a new sheet with samples filtered by a predicate function.

        Args:
            predicate: A function that takes an AvitiSample and returns bool.

        Returns:
            A new AvitiSheet with filtered samples.

        Example:
            >>> from elsheeto.models.aviti import AvitiSample, AvitiSheet
            >>> samples = [AvitiSample(sample_name="S1", index1="ATCG", project="MyProject"),
            ...            AvitiSample(sample_name="S2", index1="GCTA", project="OtherProject")]
            >>> sheet = AvitiSheet(samples=samples)
            >>> # Keep only samples from a specific project
            >>> modified_sheet = sheet.with_samples_filtered(
            ...     lambda s: s.project == "MyProject"
            ... )
            >>> len(modified_sheet.samples)
            1
        """
        new_samples = [sample for sample in self.samples if predicate(sample)]
        return self.model_copy(update={"samples": new_samples})

    def with_run_value_added(self, key: str, value: str) -> "AvitiSheet":
        """Create a new sheet with a run value added or updated.

        Args:
            key: The run value key.
            value: The run value.

        Returns:
            A new AvitiSheet with the run value added/updated.

        Example:
            >>> from elsheeto.models.aviti import AvitiSheet
            >>> sheet = AvitiSheet(samples=[])
            >>> modified_sheet = sheet.with_run_value_added("Experiment", "Test123")
            >>> modified_sheet.run_values.data["Experiment"] # doctest: +SKIP
            'Test123'
        """
        if self.run_values is None:
            new_run_values = AvitiRunValues(data=CaseInsensitiveDict({key: value}))
        else:
            new_data = CaseInsensitiveDict(self.run_values.data)
            new_data[key] = value
            new_run_values = self.run_values.model_copy(update={"data": new_data})

        return self.model_copy(update={"run_values": new_run_values})

    def with_run_values_updated(self, values: Mapping[str, str]) -> "AvitiSheet":
        """Create a new sheet with multiple run values added or updated.

        Args:
            values: Dictionary of key-value pairs to add/update.

        Returns:
            A new AvitiSheet with the run values added/updated.

        Example:
            >>> from elsheeto.models.aviti import AvitiSheet
            >>> sheet = AvitiSheet(samples=[])
            >>> modified_sheet = sheet.with_run_values_updated({
            ...     "Experiment": "Test123",
            ...     "Date": "2024-01-01"
            ... })
            >>> len(modified_sheet.run_values.data) # doctest: +SKIP
            2
        """
        if self.run_values is None:
            new_run_values = AvitiRunValues(data=CaseInsensitiveDict(values))
        else:
            new_data = CaseInsensitiveDict(self.run_values.data)
            new_data.update(values)
            new_run_values = self.run_values.model_copy(update={"data": new_data})

        return self.model_copy(update={"run_values": new_run_values})

    def with_setting_added(self, name: str, value: str, lane: str | None = None) -> "AvitiSheet":
        """Create a new sheet with a setting added.

        Args:
            name: The setting name.
            value: The setting value.
            lane: Optional lane specification.

        Returns:
            A new AvitiSheet with the setting added.

        Example:
            >>> from elsheeto.models.aviti import AvitiSheet
            >>> sheet = AvitiSheet(samples=[])
            >>> modified_sheet = sheet.with_setting_added("ReadLength", "150", "1+2")
            >>> setting = modified_sheet.settings.settings.get_by_key_and_lane("ReadLength", "1+2") # doctest: +SKIP
            >>> setting.value # doctest: +SKIP
            '150'
        """
        new_entry = AvitiSettingEntry(name=name, value=value, lane=lane)

        if self.settings is None:
            new_settings = AvitiSettings(settings=AvitiSettingEntries(entries=[new_entry]))
        else:
            new_entries = self.settings.settings.entries + [new_entry]
            new_setting_entries = AvitiSettingEntries(entries=new_entries)
            new_settings = self.settings.model_copy(update={"settings": new_setting_entries})

        return self.model_copy(update={"settings": new_settings})

    def to_csv(self, config: "WriterConfiguration | None" = None) -> str:
        """Export the sheet to CSV format.

        Args:
            config: Optional writer configuration. If None, default configuration is used.

        Returns:
            The sheet in CSV format as a string.

        Example:
            >>> from elsheeto.models.aviti import AvitiSheet
            >>> sheet = AvitiSheet(samples=[])
            >>> csv_content = sheet.to_csv()
            >>> "[Samples]" in csv_content
            True
        """
        from elsheeto.writer.aviti import AvitiCsvWriter
        from elsheeto.writer.base import WriterConfiguration

        writer = AvitiCsvWriter(config or WriterConfiguration())
        return writer.write_to_string(self)


class AvitiSheetBuilder:
    """Mutable builder for constructing AvitiSheet instances.

    This builder provides a fluent API for complex modifications while maintaining
    type safety and validation. The builder is mutable during construction but
    produces immutable AvitiSheet instances.

    Examples:
        Create a new sheet from scratch:

        >>> builder = AvitiSheetBuilder()
        >>> sheet = (builder
        ...     .add_sample(AvitiSample(sample_name="Sample1", index1="ATCG"))
        ...     .add_run_value("Experiment", "Test")
        ...     .build())

        Modify an existing sheet:

        >>> from elsheeto.models.aviti import AvitiSample, AvitiSheet
        >>> existing_sheet = AvitiSheet(samples=[AvitiSample(sample_name="Old", index1="AAAA")])
        >>> builder = AvitiSheetBuilder.from_sheet(existing_sheet)
        >>> modified = (builder
        ...     .remove_sample_by_name("Old")
        ...     .add_sample(AvitiSample(sample_name="NewSample", index1="GCTA"))
        ...     .build())
    """

    def __init__(self) -> None:
        """Initialize an empty builder."""
        self._samples: list[AvitiSample] = []
        self._run_values: dict[str, str] = {}
        self._run_values_extra: dict[str, str] = {}
        self._settings_entries: list[AvitiSettingEntry] = []
        self._settings_extra: dict[str, str] = {}

    @classmethod
    def from_sheet(cls, sheet: "AvitiSheet") -> "AvitiSheetBuilder":
        """Create a builder initialized with data from an existing sheet.

        Args:
            sheet: The existing AvitiSheet to copy data from.

        Returns:
            A new builder containing the sheet's data.
        """
        builder = cls()

        # Copy samples
        builder._samples = list(sheet.samples)

        # Copy run values
        if sheet.run_values:
            builder._run_values = dict(sheet.run_values.data.items())
            builder._run_values_extra = dict(sheet.run_values.extra_metadata.items())

        # Copy settings
        if sheet.settings:
            builder._settings_entries = list(sheet.settings.settings.entries)
            builder._settings_extra = dict(sheet.settings.extra_metadata.items())

        return builder

    def add_sample(self, sample: AvitiSample) -> "AvitiSheetBuilder":
        """Add a sample to the sheet.

        Args:
            sample: The sample to add.

        Returns:
            This builder for method chaining.
        """
        self._samples.append(sample)
        return self

    def add_samples(self, samples: list[AvitiSample]) -> "AvitiSheetBuilder":
        """Add multiple samples to the sheet.

        Args:
            samples: The samples to add.

        Returns:
            This builder for method chaining.
        """
        self._samples.extend(samples)
        return self

    def remove_sample(self, sample: AvitiSample) -> "AvitiSheetBuilder":
        """Remove a sample from the sheet.

        Args:
            sample: The sample to remove.

        Returns:
            This builder for method chaining.

        Raises:
            ValueError: If the sample is not found.
        """
        try:
            self._samples.remove(sample)
        except ValueError:
            raise ValueError(f"Sample not found: {sample}")
        return self

    def remove_sample_by_name(self, sample_name: str) -> "AvitiSheetBuilder":
        """Remove a sample by its name.

        Args:
            sample_name: The name of the sample to remove.

        Returns:
            This builder for method chaining.

        Raises:
            ValueError: If no sample with the given name is found.
        """
        for i, sample in enumerate(self._samples):
            if sample.sample_name == sample_name:
                del self._samples[i]
                return self
        raise ValueError(f"No sample found with name: {sample_name}")

    def remove_samples_by_project(self, project: str) -> "AvitiSheetBuilder":
        """Remove all samples with the specified project.

        Args:
            project: The project name to match.

        Returns:
            This builder for method chaining.
        """
        self._samples = [s for s in self._samples if s.project != project]
        return self

    def update_sample_by_name(self, sample_name: str, **updates) -> "AvitiSheetBuilder":
        """Update a sample by its name.

        Args:
            sample_name: The name of the sample to update.
            **updates: Fields to update on the sample.

        Returns:
            This builder for method chaining.

        Raises:
            ValueError: If no sample with the given name is found.
        """
        for i, sample in enumerate(self._samples):
            if sample.sample_name == sample_name:
                self._samples[i] = sample.model_copy(update=updates)
                return self
        raise ValueError(f"No sample found with name: {sample_name}")

    def clear_samples(self) -> "AvitiSheetBuilder":
        """Remove all samples from the sheet.

        Returns:
            This builder for method chaining.
        """
        self._samples.clear()
        return self

    def add_run_value(self, key: str, value: str) -> "AvitiSheetBuilder":
        """Add or update a run value.

        Args:
            key: The run value key.
            value: The run value.

        Returns:
            This builder for method chaining.
        """
        self._run_values[key] = value
        return self

    def add_run_values(self, values: Mapping[str, str]) -> "AvitiSheetBuilder":
        """Add or update multiple run values.

        Args:
            values: Dictionary of key-value pairs to add.

        Returns:
            This builder for method chaining.
        """
        self._run_values.update(values)
        return self

    def remove_run_value(self, key: str) -> "AvitiSheetBuilder":
        """Remove a run value.

        Args:
            key: The key to remove.

        Returns:
            This builder for method chaining.

        Raises:
            KeyError: If the key is not found.
        """
        del self._run_values[key]
        return self

    def clear_run_values(self) -> "AvitiSheetBuilder":
        """Remove all run values.

        Returns:
            This builder for method chaining.
        """
        self._run_values.clear()
        self._run_values_extra.clear()
        return self

    def add_setting(self, name: str, value: str, lane: str | None = None) -> "AvitiSheetBuilder":
        """Add a setting entry.

        Args:
            name: The setting name.
            value: The setting value.
            lane: Optional lane specification.

        Returns:
            This builder for method chaining.
        """
        entry = AvitiSettingEntry(name=name, value=value, lane=lane)
        self._settings_entries.append(entry)
        return self

    def add_settings(self, settings: list[AvitiSettingEntry]) -> "AvitiSheetBuilder":
        """Add multiple setting entries.

        Args:
            settings: List of setting entries to add.

        Returns:
            This builder for method chaining.
        """
        self._settings_entries.extend(settings)
        return self

    def remove_settings_by_name(self, name: str) -> "AvitiSheetBuilder":
        """Remove all settings with the specified name.

        Args:
            name: The setting name to remove.

        Returns:
            This builder for method chaining.
        """
        self._settings_entries = [entry for entry in self._settings_entries if entry.name.lower() != name.lower()]
        return self

    def remove_settings_by_name_and_lane(self, name: str, lane: str | None) -> "AvitiSheetBuilder":
        """Remove settings with exact name and lane match.

        Args:
            name: The setting name to remove.
            lane: The lane specification to match.

        Returns:
            This builder for method chaining.
        """
        self._settings_entries = [
            entry for entry in self._settings_entries if not (entry.name.lower() == name.lower() and entry.lane == lane)
        ]
        return self

    def clear_settings(self) -> "AvitiSheetBuilder":
        """Remove all settings.

        Returns:
            This builder for method chaining.
        """
        self._settings_entries.clear()
        self._settings_extra.clear()
        return self

    def build(self) -> "AvitiSheet":
        """Build the immutable AvitiSheet instance.

        Returns:
            A new AvitiSheet with the builder's data.

        Raises:
            ValidationError: If the data is invalid.
        """
        # Build run values section
        run_values = None
        if self._run_values or self._run_values_extra:
            run_values = AvitiRunValues(
                data=CaseInsensitiveDict(self._run_values), extra_metadata=CaseInsensitiveDict(self._run_values_extra)
            )

        # Build settings section
        settings = None
        if self._settings_entries or self._settings_extra:
            settings = AvitiSettings(
                settings=AvitiSettingEntries(entries=self._settings_entries.copy()),
                extra_metadata=CaseInsensitiveDict(self._settings_extra),
            )

        # Build the sheet
        return AvitiSheet(run_values=run_values, settings=settings, samples=self._samples.copy())
