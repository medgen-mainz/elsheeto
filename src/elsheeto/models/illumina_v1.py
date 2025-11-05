"""Illumina sample sheet v1 specific models.

The Stage 2 results are converted into these models in Stage 3.
"""

from typing import TYPE_CHECKING, Annotated, Mapping

from pydantic import BaseModel, ConfigDict, Field

from elsheeto.models.utils import CaseInsensitiveDict

if TYPE_CHECKING:
    from elsheeto.writer.base import WriterConfiguration


class IlluminaHeader(BaseModel):
    """Representation of the Illumina v1 `Header` section."""

    #: Optional `IEMFileVersion` field.
    iem_file_version: str | None = None
    #: Optional `Investigator Name` field.
    investigator_name: str | None = None
    #: Optional `Experiment Name` field.
    experiment_name: str | None = None
    #: Optional `Date` field.
    date: str | None = None
    #: Required `Workflow` field.
    workflow: str = "GenerateFASTQ"
    #: Optional `Application` field.
    application: str | None = None
    #: Optional `Instrument Type` field.
    instrument_type: str | None = None
    #: Optional `Assay` field.
    assay: str | None = None
    #: Optional `Index Adapters` field.
    index_adapters: str | None = None
    #: Optional `Description` field.
    description: str | None = None
    #: `Chemistry` field, must be set to `amplicon` (case insensitive)
    #: for dual indexing.
    chemistry: str | None = None
    #: Optional `Run` field.
    run: str | None = None

    #: Optional extra metadata for fields not explicitly defined.
    extra_metadata: CaseInsensitiveDict = Field(default_factory=CaseInsensitiveDict)

    #: Model configuration.
    model_config = ConfigDict(frozen=True)


class IlluminaReads(BaseModel):
    """Representation of the Illumina v1 `Reads` section."""

    #: List of read lengths.
    read_lengths: list[int]

    #: Model configuration.
    model_config = ConfigDict(frozen=True)


class IlluminaSettings(BaseModel):
    """Representation of the Illumina v1 `Settings` section.

    Note that these are mainly used for running old Illumina pipelines and
    we just store key/value maps here.
    """

    #: Key/value data in the settings section.
    data: CaseInsensitiveDict

    #: Optional extra metadata.
    extra_metadata: Annotated[CaseInsensitiveDict, Field(default_factory=CaseInsensitiveDict)]

    #: Model configuration.
    model_config = ConfigDict(frozen=True)


class IlluminaSample(BaseModel):
    """One entry in the Illumina v1 `Data` section."""

    #: Optional `Lane` field.
    lane: int | None = None
    #: `Sample_ID` field.
    sample_id: str
    #: Optional `Sample_Name` field.
    sample_name: str | None = None
    #: Optional `Sample_Plate` field.
    sample_plate: str | None = None
    #: Optional `Sample_Well` field.
    sample_well: str | None = None
    #: Optional `Index_Plate_Well` field.
    index_plate_well: str | None = None
    #: Optional `Inline_ID` field.
    inline_id: str | None = None
    #: Optional `I7_Index_ID` field.
    i7_index_id: str | None = None
    #: `index` field.
    index: str | None = None
    #: Optional `I5_Index_ID` field.
    i5_index_id: str | None = None
    #: `index2` field.
    index2: str | None = None
    #: Optional `Sample_Project` field.
    sample_project: str | None = None
    #: Optional `Description` field.
    description: str | None = None

    #: Optional extra metadata for fields not explicitly defined.
    extra_metadata: CaseInsensitiveDict = Field(default_factory=CaseInsensitiveDict)

    #: Model configuration.
    model_config = ConfigDict(frozen=True)


class IlluminaSampleSheet(BaseModel):
    """Representation of an Illumina v1 sample sheet.

    See Illumina documentation for details.
    """

    #: The Illumina `Header` section.
    header: IlluminaHeader
    #: The Illumina `Reads` section.
    reads: IlluminaReads | None
    #: The Illumina v1 `Settings` section.
    settings: IlluminaSettings | None
    #: The Illumina `Data` section.
    data: list[IlluminaSample] = Field(default_factory=list)

    #: Model configuration.
    model_config = ConfigDict(frozen=True)

    def with_sample_added(self, sample: IlluminaSample, position: int | None = None) -> "IlluminaSampleSheet":
        """Create a new sheet with an additional sample.

        Args:
            sample: The sample to add.
            position: Optional position to insert the sample. If None, appends to the end.

        Returns:
            A new IlluminaSampleSheet with the sample added.

        Example:
            >>> from elsheeto.models.illumina_v1 import IlluminaSample, IlluminaSampleSheet, IlluminaHeader, IlluminaReads
            >>> header = IlluminaHeader()
            >>> sheet = IlluminaSampleSheet(header=header, reads=None, settings=None, data=[])
            >>> new_sample = IlluminaSample(sample_id="Test", sample_name="TestSample")
            >>> modified_sheet = sheet.with_sample_added(new_sample)
            >>> len(modified_sheet.data)
            1
        """
        if position is None:
            new_data = self.data + [sample]
        else:
            new_data = list(self.data)
            new_data.insert(position, sample)
        return self.model_copy(update={"data": new_data})

    def with_sample_removed(self, sample_identifier: str | int) -> "IlluminaSampleSheet":
        """Create a new sheet with a sample removed by Sample_ID or index.

        Args:
            sample_identifier: The Sample_ID (string) or index (int) of the sample to remove.

        Returns:
            A new IlluminaSampleSheet with the sample removed.

        Raises:
            ValueError: If no sample with the given Sample_ID is found.
            IndexError: If the sample index is out of range.

        Example:
            >>> from elsheeto.models.illumina_v1 import IlluminaSample, IlluminaSampleSheet, IlluminaHeader
            >>> header = IlluminaHeader()
            >>> sample = IlluminaSample(sample_id="Test", sample_name="TestSample")
            >>> sheet = IlluminaSampleSheet(header=header, reads=None, settings=None, data=[sample])
            >>> modified_sheet = sheet.with_sample_removed("Test")
            >>> len(modified_sheet.data)
            0
        """
        if isinstance(sample_identifier, int):
            # Remove by index
            if sample_identifier < 0 or sample_identifier >= len(self.data):
                raise IndexError(f"Sample index {sample_identifier} is out of range")
            new_data = list(self.data)
            del new_data[sample_identifier]
        else:
            # Remove by Sample_ID
            new_data = []
            found = False
            for sample in self.data:
                if sample.sample_id == sample_identifier:
                    found = True
                else:
                    new_data.append(sample)

            if not found:
                raise ValueError(f"Sample with ID '{sample_identifier}' not found")

        return self.model_copy(update={"data": new_data})

    def with_sample_modified(self, sample_identifier: str | int, **updates) -> "IlluminaSampleSheet":
        """Create a new sheet with a sample modified by Sample_ID or index.

        Args:
            sample_identifier: The Sample_ID (string) or index (int) of the sample to modify.
            **updates: Fields to update on the sample.

        Returns:
            A new IlluminaSampleSheet with the sample modified.

        Raises:
            ValueError: If no sample with the given Sample_ID is found or invalid field provided.
            IndexError: If the sample index is out of range.

        Example:
            >>> from elsheeto.models.illumina_v1 import IlluminaSample, IlluminaSampleSheet, IlluminaHeader
            >>> header = IlluminaHeader()
            >>> sample = IlluminaSample(sample_id="Test", sample_name="TestSample")
            >>> sheet = IlluminaSampleSheet(header=header, reads=None, settings=None, data=[sample])
            >>> modified_sheet = sheet.with_sample_modified("Test", sample_project="NewProject")
            >>> modified_sheet.data[0].sample_project
            'NewProject'
        """
        # Validate that all update fields are valid for IlluminaSample
        if updates:
            sample_fields = set(IlluminaSample.model_fields.keys())
            for field in updates.keys():
                if field not in sample_fields:
                    raise ValueError(f"Invalid field '{field}' for IlluminaSample")

        if isinstance(sample_identifier, int):
            # Modify by index
            if sample_identifier < 0 or sample_identifier >= len(self.data):
                raise IndexError(f"Sample index {sample_identifier} is out of range")
            new_data = list(self.data)
            new_data[sample_identifier] = new_data[sample_identifier].model_copy(update=updates)
        else:
            # Modify by Sample_ID
            new_data = []
            found = False
            for sample in self.data:
                if sample.sample_id == sample_identifier:
                    found = True
                    new_data.append(sample.model_copy(update=updates))
                else:
                    new_data.append(sample)

            if not found:
                raise ValueError(f"Sample with ID '{sample_identifier}' not found")

        return self.model_copy(update={"data": new_data})

    def with_samples_filtered(self, predicate) -> "IlluminaSampleSheet":
        """Create a new sheet with samples filtered by a predicate function.

        Args:
            predicate: A function that takes an IlluminaSample and returns bool.

        Returns:
            A new IlluminaSampleSheet with filtered samples.

        Example:
            >>> from elsheeto.models.illumina_v1 import IlluminaSample, IlluminaSampleSheet, IlluminaHeader
            >>> header = IlluminaHeader()
            >>> samples = [IlluminaSample(sample_id="S1", sample_project="ProjectA"),
            ...            IlluminaSample(sample_id="S2", sample_project="ProjectB")]
            >>> sheet = IlluminaSampleSheet(header=header, reads=None, settings=None, data=samples)
            >>> # Keep only samples from ProjectA
            >>> modified_sheet = sheet.with_samples_filtered(
            ...     lambda s: s.sample_project == "ProjectA"
            ... )
            >>> len(modified_sheet.data)
            1
        """
        new_data = [sample for sample in self.data if predicate(sample)]
        return self.model_copy(update={"data": new_data})

    def with_header_field_updated(self, field_name: str, value: str | None) -> "IlluminaSampleSheet":
        """Create a new sheet with a header field updated.

        Args:
            field_name: The name of the header field to update.
            value: The new value for the field.

        Returns:
            A new IlluminaSampleSheet with the header field updated.

        Example:
            >>> from elsheeto.models.illumina_v1 import IlluminaSampleSheet, IlluminaHeader
            >>> header = IlluminaHeader()
            >>> sheet = IlluminaSampleSheet(header=header, reads=None, settings=None, data=[])
            >>> modified_sheet = sheet.with_header_field_updated("experiment_name", "NewExperiment")
            >>> modified_sheet.header.experiment_name
            'NewExperiment'
        """
        # Convert field_name to the correct attribute name (snake_case)
        field_mapping = {
            "IEMFileVersion": "iem_file_version",
            "Investigator Name": "investigator_name",
            "Experiment Name": "experiment_name",
            "Date": "date",
            "Workflow": "workflow",
            "Application": "application",
            "Instrument Type": "instrument_type",
            "Assay": "assay",
            "Index Adapters": "index_adapters",
            "Description": "description",
            "Chemistry": "chemistry",
            "Run": "run",
        }

        # Check if this is a mapped header field first
        if field_name in field_mapping:
            attr_name = field_mapping[field_name]
            new_header = self.header.model_copy(update={attr_name: value})
        else:
            # Check if it's a direct attribute (snake_case version)
            attr_name = field_name.lower().replace(" ", "_")
            header_fields = set(IlluminaHeader.model_fields.keys())
            if attr_name in header_fields:
                new_header = self.header.model_copy(update={attr_name: value})
            else:
                # Update extra_metadata
                new_extra_metadata = CaseInsensitiveDict(self.header.extra_metadata)
                new_extra_metadata[field_name] = value
                new_header = self.header.model_copy(update={"extra_metadata": new_extra_metadata})

        return self.model_copy(update={"header": new_header})

    def with_header_updated(self, **updates) -> "IlluminaSampleSheet":
        """Create a new sheet with multiple header fields updated.

        Args:
            **updates: Fields to update on the header.

        Returns:
            A new IlluminaSampleSheet with the header updated.

        Example:
            >>> from elsheeto.models.illumina_v1 import IlluminaSampleSheet, IlluminaHeader
            >>> header = IlluminaHeader()
            >>> sheet = IlluminaSampleSheet(header=header, reads=None, settings=None, data=[])
            >>> modified_sheet = sheet.with_header_updated(
            ...     experiment_name="NewExperiment",
            ...     investigator_name="Dr. Smith"
            ... )
            >>> modified_sheet.header.experiment_name
            'NewExperiment'
        """
        new_header = self.header.model_copy(update=updates)
        return self.model_copy(update={"header": new_header})

    def with_reads_updated(self, read_lengths: list[int]) -> "IlluminaSampleSheet":
        """Create a new sheet with read lengths updated.

        Args:
            read_lengths: List of read lengths.

        Returns:
            A new IlluminaSampleSheet with the reads section updated.

        Example:
            >>> from elsheeto.models.illumina_v1 import IlluminaSampleSheet, IlluminaHeader
            >>> header = IlluminaHeader()
            >>> sheet = IlluminaSampleSheet(header=header, reads=None, settings=None, data=[])
            >>> modified_sheet = sheet.with_reads_updated([150, 150])
            >>> modified_sheet.reads.read_lengths # doctest: +SKIP
            [150, 150]
        """
        new_reads = IlluminaReads(read_lengths=read_lengths)
        return self.model_copy(update={"reads": new_reads})

    def with_setting_added(self, key: str, value: str) -> "IlluminaSampleSheet":
        """Create a new sheet with a setting added or updated.

        Args:
            key: The setting key.
            value: The setting value.

        Returns:
            A new IlluminaSampleSheet with the setting added/updated.

        Example:
            >>> from elsheeto.models.illumina_v1 import IlluminaSampleSheet, IlluminaHeader
            >>> header = IlluminaHeader()
            >>> sheet = IlluminaSampleSheet(header=header, reads=None, settings=None, data=[])
            >>> modified_sheet = sheet.with_setting_added("Adapter", "ATCG")
            >>> modified_sheet.settings.data["Adapter"] # doctest: +SKIP
            'ATCG'
        """
        if self.settings is None:
            new_settings = IlluminaSettings(
                data=CaseInsensitiveDict({key: value}), extra_metadata=CaseInsensitiveDict()
            )
        else:
            new_data = CaseInsensitiveDict(self.settings.data)
            new_data[key] = value
            new_settings = self.settings.model_copy(update={"data": new_data})

        return self.model_copy(update={"settings": new_settings})

    def with_settings_updated(self, settings: Mapping[str, str]) -> "IlluminaSampleSheet":
        """Create a new sheet with multiple settings added or updated.

        Args:
            settings: Dictionary of key-value pairs to add/update.

        Returns:
            A new IlluminaSampleSheet with the settings added/updated.

        Example:
            >>> from elsheeto.models.illumina_v1 import IlluminaSampleSheet, IlluminaHeader
            >>> header = IlluminaHeader()
            >>> sheet = IlluminaSampleSheet(header=header, reads=None, settings=None, data=[])
            >>> modified_sheet = sheet.with_settings_updated({
            ...     "Adapter": "ATCG",
            ...     "TrimAdapter": "True"
            ... })
            >>> len(modified_sheet.settings.data) # doctest: +SKIP
            2
        """
        if self.settings is None:
            new_settings = IlluminaSettings(data=CaseInsensitiveDict(settings), extra_metadata=CaseInsensitiveDict())
        else:
            new_data = CaseInsensitiveDict(self.settings.data)
            new_data.update(settings)
            new_settings = self.settings.model_copy(update={"data": new_data})

        return self.model_copy(update={"settings": new_settings})

    def with_settings_field_updated(self, key: str, value: str) -> "IlluminaSampleSheet":
        """Create a new sheet with a single settings field updated.

        Args:
            key: The settings key to update.
            value: The new value for the settings key.

        Returns:
            A new IlluminaSampleSheet with the settings field updated.

        Example:
            >>> from elsheeto.models.illumina_v1 import IlluminaSampleSheet, IlluminaHeader
            >>> header = IlluminaHeader()
            >>> sheet = IlluminaSampleSheet(header=header, reads=None, settings=None, samples=[])
            >>> modified_sheet = sheet.with_settings_field_updated("Adapter", "ATCG")
            >>> modified_sheet.settings.data["Adapter"] # doctest: +SKIP
            'ATCG'
        """
        return self.with_settings_updated({key: value})

    def to_csv(self, config: "WriterConfiguration | None" = None) -> str:
        """Export the sheet to CSV format.

        Args:
            config: Optional writer configuration. If None, default configuration is used.

        Returns:
            The sheet in CSV format as a string.

        Example:
            >>> from elsheeto.models.illumina_v1 import IlluminaSampleSheet, IlluminaHeader
            >>> header = IlluminaHeader()
            >>> sheet = IlluminaSampleSheet(header=header, reads=None, settings=None, data=[])
            >>> csv_content = sheet.to_csv()
            >>> "[Header]" in csv_content
            True
        """
        from elsheeto.writer.base import WriterConfiguration
        from elsheeto.writer.illumina_v1 import IlluminaCsvWriter

        writer = IlluminaCsvWriter(config or WriterConfiguration())
        return writer.write_to_string(self)


class IlluminaSheetBuilder:
    """Mutable builder for constructing IlluminaSampleSheet instances.

    This builder provides a fluent API for complex modifications while maintaining
    type safety and validation. The builder is mutable during construction but
    produces immutable IlluminaSampleSheet instances.

    Examples:
        Create a new sheet from scratch:

        >>> from elsheeto.models.illumina_v1 import IlluminaSheetBuilder, IlluminaSample
        >>> builder = IlluminaSheetBuilder()
        >>> sheet = (builder
        ...     .add_sample(IlluminaSample(sample_id="Sample1", sample_name="Test"))
        ...     .set_header_field("experiment_name", "Test")
        ...     .build())

        Modify an existing sheet:

        >>> from elsheeto.models.illumina_v1 import IlluminaSample, IlluminaSampleSheet, IlluminaHeader
        >>> header = IlluminaHeader()
        >>> existing_sheet = IlluminaSampleSheet(header=header, reads=None, settings=None, data=[IlluminaSample(sample_id="Old")])
        >>> builder = IlluminaSheetBuilder.from_sheet(existing_sheet)
        >>> modified = (builder
        ...     .remove_sample_by_id("Old")
        ...     .add_sample(IlluminaSample(sample_id="NewSample", sample_name="New"))
        ...     .build())
    """

    def __init__(self) -> None:
        """Initialize an empty builder."""
        self._samples: list[IlluminaSample] = []
        self._header_fields: dict[str, str | None] = {}
        self._read_lengths: list[int] = []
        self._settings: dict[str, str] = {}
        self._settings_extra: dict[str, str] = {}

    @classmethod
    def from_sheet(cls, sheet: "IlluminaSampleSheet") -> "IlluminaSheetBuilder":
        """Create a builder initialized with data from an existing sheet.

        Args:
            sheet: The existing IlluminaSampleSheet to copy data from.

        Returns:
            A new builder containing the sheet's data.
        """
        builder = cls()

        # Copy samples
        builder._samples = list(sheet.data)

        # Copy header fields
        header_dict = sheet.header.model_dump(exclude={"extra_metadata"})
        builder._header_fields = {k: v for k, v in header_dict.items() if v is not None}

        # Copy read lengths
        if sheet.reads:
            builder._read_lengths = list(sheet.reads.read_lengths)

        # Copy settings
        if sheet.settings:
            builder._settings = dict(sheet.settings.data.items())
            builder._settings_extra = dict(sheet.settings.extra_metadata.items())

        return builder

    def add_sample(self, sample: IlluminaSample) -> "IlluminaSheetBuilder":
        """Add a sample to the sheet.

        Args:
            sample: The sample to add.

        Returns:
            This builder for method chaining.
        """
        self._samples.append(sample)
        return self

    def add_samples(self, samples: list[IlluminaSample]) -> "IlluminaSheetBuilder":
        """Add multiple samples to the sheet.

        Args:
            samples: The samples to add.

        Returns:
            This builder for method chaining.
        """
        self._samples.extend(samples)
        return self

    def remove_sample(self, sample: IlluminaSample | str | int) -> "IlluminaSheetBuilder":
        """Remove a sample from the sheet.

        Args:
            sample: Sample to remove. Can be:
                - IlluminaSample instance
                - str: sample_id to find and remove
                - int: index of sample to remove

        Returns:
            This builder for method chaining.

        Raises:
            ValueError: If sample is not found or index is out of range.
        """
        if isinstance(sample, IlluminaSample):
            try:
                self._samples.remove(sample)
            except ValueError:
                raise ValueError(f"Sample not found: {sample}")
        elif isinstance(sample, str):
            return self.remove_sample_by_id(sample)
        elif isinstance(sample, int):
            if 0 <= sample < len(self._samples):
                self._samples.pop(sample)
            else:
                raise IndexError(f"Sample index {sample} is out of range")
        else:
            raise ValueError("Sample must be IlluminaSample, str (sample_id), or int (index)")

        return self

    def remove_sample_by_id(self, sample_id: str) -> "IlluminaSheetBuilder":
        """Remove a sample by its Sample_ID.

        Args:
            sample_id: The Sample_ID of the sample to remove.

        Returns:
            This builder for method chaining.

        Raises:
            ValueError: If no sample with the given Sample_ID is found.
        """
        for i, sample in enumerate(self._samples):
            if sample.sample_id == sample_id:
                del self._samples[i]
                return self
        raise ValueError(f"Sample with ID '{sample_id}' not found")

    def remove_samples_by_project(self, project: str) -> "IlluminaSheetBuilder":
        """Remove all samples with the specified Sample_Project.

        Args:
            project: The Sample_Project name to match.

        Returns:
            This builder for method chaining.
        """
        self._samples = [s for s in self._samples if s.sample_project != project]
        return self

    def update_sample_by_id(self, sample_id: str, **updates) -> "IlluminaSheetBuilder":
        """Update a sample by its Sample_ID.

        Args:
            sample_id: The Sample_ID of the sample to update.
            **updates: Fields to update on the sample.

        Returns:
            This builder for method chaining.

        Raises:
            ValueError: If no sample with the given Sample_ID is found or invalid field provided.
        """
        # Validate field names first
        valid_fields = set(IlluminaSample.model_fields.keys())
        for key in updates:
            if key not in valid_fields:
                raise ValueError(f"Invalid field '{key}' for IlluminaSample")

        for i, sample in enumerate(self._samples):
            if sample.sample_id == sample_id:
                self._samples[i] = sample.model_copy(update=updates)
                return self
        raise ValueError(f"Sample with ID '{sample_id}' not found")

    def clear_samples(self) -> "IlluminaSheetBuilder":
        """Remove all samples from the sheet.

        Returns:
            This builder for method chaining.
        """
        self._samples.clear()
        return self

    def set_header_field(self, field_name: str, value: str | None) -> "IlluminaSheetBuilder":
        """Set a header field value.

        Args:
            field_name: The name of the header field (snake_case or display name).
            value: The value to set.

        Returns:
            This builder for method chaining.
        """
        # Convert display names to snake_case if needed
        field_mapping = {
            "IEMFileVersion": "iem_file_version",
            "Investigator Name": "investigator_name",
            "Experiment Name": "experiment_name",
            "Date": "date",
            "Workflow": "workflow",
            "Application": "application",
            "Instrument Type": "instrument_type",
            "Assay": "assay",
            "Index Adapters": "index_adapters",
            "Description": "description",
            "Chemistry": "chemistry",
            "Run": "run",
        }

        # Use the mapped name if it's a known field, otherwise preserve original case
        if field_name in field_mapping:
            attr_name = field_mapping[field_name]
        else:
            # Check if it's a known header field by checking the snake_case version
            snake_case_name = field_name.lower().replace(" ", "_")
            valid_header_fields = set(IlluminaHeader.model_fields.keys()) - {"extra_metadata"}
            if snake_case_name in valid_header_fields:
                attr_name = snake_case_name
            else:
                # It's an extra metadata field, preserve original case
                attr_name = field_name

        self._header_fields[attr_name] = value
        return self

    def set_header_fields(self, fields: Mapping[str, str | None]) -> "IlluminaSheetBuilder":
        """Set multiple header fields.

        Args:
            fields: Dictionary of field names to values.

        Returns:
            This builder for method chaining.
        """
        for field_name, value in fields.items():
            self.set_header_field(field_name, value)
        return self

    def clear_header_fields(self) -> "IlluminaSheetBuilder":
        """Clear all header fields (except workflow which has a default).

        Returns:
            This builder for method chaining.
        """
        self._header_fields.clear()
        return self

    def set_read_lengths(self, read_lengths: list[int]) -> "IlluminaSheetBuilder":
        """Set the read lengths.

        Args:
            read_lengths: List of read lengths.

        Returns:
            This builder for method chaining.
        """
        self._read_lengths = list(read_lengths)
        return self

    def add_read_length(self, read_length: int) -> "IlluminaSheetBuilder":
        """Add a read length.

        Args:
            read_length: The read length to add.

        Returns:
            This builder for method chaining.
        """
        self._read_lengths.append(read_length)
        return self

    def clear_read_lengths(self) -> "IlluminaSheetBuilder":
        """Clear all read lengths.

        Returns:
            This builder for method chaining.
        """
        self._read_lengths.clear()
        return self

    def add_setting(self, key: str, value: str) -> "IlluminaSheetBuilder":
        """Add or update a setting.

        Args:
            key: The setting key.
            value: The setting value.

        Returns:
            This builder for method chaining.
        """
        self._settings[key] = value
        return self

    def add_settings(self, settings: Mapping[str, str]) -> "IlluminaSheetBuilder":
        """Add or update multiple settings.

        Args:
            settings: Dictionary of key-value pairs to add.

        Returns:
            This builder for method chaining.
        """
        self._settings.update(settings)
        return self

    def update_settings_field(self, key: str, value: str) -> "IlluminaSheetBuilder":
        """Update a single settings field.

        Args:
            key: The settings key to update.
            value: The new value for the settings key.

        Returns:
            This builder for method chaining.

        Raises:
            ValueError: If no settings have been set.
        """
        if not self._settings and not self._settings_extra:
            raise ValueError("No settings set. Use set_settings() first")
        self._settings[key] = value
        return self

    def remove_setting(self, key: str) -> "IlluminaSheetBuilder":
        """Remove a setting.

        Args:
            key: The key to remove.

        Returns:
            This builder for method chaining.

        Raises:
            KeyError: If the key is not found.
        """
        del self._settings[key]
        return self

    def clear_settings(self) -> "IlluminaSheetBuilder":
        """Remove all settings.

        Returns:
            This builder for method chaining.
        """
        self._settings.clear()
        self._settings_extra.clear()
        return self

    # Additional methods needed by tests
    def set_header(self, header: IlluminaHeader) -> "IlluminaSheetBuilder":
        """Set the complete header by copying its fields."""
        header_dict = header.model_dump()
        # Separate standard fields from extra_metadata
        extra_metadata = header_dict.pop("extra_metadata", {})

        # Update standard header fields - use model_fields to check valid fields
        valid_fields = set(IlluminaHeader.model_fields.keys())
        for key, value in header_dict.items():
            if key in valid_fields:
                self._header_fields[key] = value

        # Update extra metadata (flatten to regular dict)
        for key, value in extra_metadata.items():
            self._header_fields[key] = value
        return self

    def update_header_field(self, field_name: str, value: str | None) -> "IlluminaSheetBuilder":
        """Update a specific header field. Alias for set_header_field."""
        if not self._header_fields:
            raise ValueError("No header set. Use set_header() first")
        return self.set_header_field(field_name, value)

    def set_reads(self, reads: IlluminaReads) -> "IlluminaSheetBuilder":
        """Set the complete reads configuration."""
        self._read_lengths = reads.read_lengths.copy()
        return self

    def update_reads(self, read_lengths: list[int]) -> "IlluminaSheetBuilder":
        """Update the read lengths. Alias for set_read_lengths."""
        if not self._read_lengths:
            raise ValueError("No reads set. Use set_reads() first")
        return self.set_read_lengths(read_lengths)

    def set_settings(self, settings: IlluminaSettings) -> "IlluminaSheetBuilder":
        """Set the complete settings by copying its data."""
        self._settings.clear()
        self._settings_extra.clear()

        # Copy standard settings
        self._settings.update(dict(settings.data))

        # Copy extra metadata
        self._settings_extra.update(dict(settings.extra_metadata))
        return self

    def update_sample(self, identifier: str | int, **updates) -> "IlluminaSheetBuilder":
        """Update a sample by identifier."""
        if isinstance(identifier, str):
            return self.update_sample_by_id(identifier, **updates)
        elif isinstance(identifier, int):
            # Update by index
            if identifier < 0 or identifier >= len(self._samples):
                raise ValueError(f"Sample index {identifier} out of range")

            sample = self._samples[identifier]
            # Create updated sample
            sample_dict = sample.model_dump()
            sample_dict.update(updates)

            # Validate updates - check if the fields exist in the IlluminaSample model
            valid_fields = set(IlluminaSample.model_fields.keys())
            for key in updates:
                if key not in valid_fields:  # pragma: no cover
                    raise ValueError(f"Invalid field: {key}")

            updated_sample = IlluminaSample(**sample_dict)
            self._samples[identifier] = updated_sample
            return self
        else:  # pragma: no cover
            raise AssertionError("Identifier must be str (sample_id) or int (index)")

    def build(self) -> "IlluminaSampleSheet":
        """Build the immutable IlluminaSampleSheet instance.

        Returns:
            A new IlluminaSampleSheet with the builder's data.

        Raises:
            ValidationError: If the data is invalid.
        """
        # Build header section - always create header (required by model)
        header_data = {
            "iem_file_version": None,
            "investigator_name": None,
            "experiment_name": None,
            "date": None,
            "workflow": "GenerateFASTQ",  # Default value
            "application": None,
            "instrument_type": None,
            "assay": None,
            "index_adapters": None,
            "description": None,
            "chemistry": None,
            "run": None,
            "extra_metadata": CaseInsensitiveDict(),
        }

        # Separate standard fields from extra metadata
        valid_header_fields = set(IlluminaHeader.model_fields.keys()) - {"extra_metadata"}
        extra_metadata = CaseInsensitiveDict()

        for key, value in self._header_fields.items():
            if key in valid_header_fields:
                header_data[key] = value
            else:
                extra_metadata[key] = value

        header_data["extra_metadata"] = extra_metadata
        header = IlluminaHeader(**header_data)

        # Build reads section
        reads = None
        if self._read_lengths:
            reads = IlluminaReads(read_lengths=self._read_lengths)

        # Build settings section
        settings = None
        if self._settings or self._settings_extra:
            settings = IlluminaSettings(
                data=CaseInsensitiveDict(self._settings), extra_metadata=CaseInsensitiveDict(self._settings_extra)
            )

        # Build the sheet
        return IlluminaSampleSheet(header=header, reads=reads, settings=settings, data=self._samples.copy())
