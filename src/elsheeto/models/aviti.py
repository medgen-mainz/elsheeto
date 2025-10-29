"""Aviti sample sheet (aka Sequencing Manifest) specific models.

The Stage 2 results are converted into these models in Stage 3.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from elsheeto.models.utils import CaseInsensitiveDict


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
    extra_metadata: CaseInsensitiveDict = Field(default_factory=lambda: CaseInsensitiveDict({}))

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
    data: CaseInsensitiveDict = Field(default_factory=lambda: CaseInsensitiveDict({}))
    #: Optional extra metadata.
    extra_metadata: CaseInsensitiveDict = Field(default_factory=lambda: CaseInsensitiveDict({}))

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
    extra_metadata: CaseInsensitiveDict = Field(default_factory=lambda: CaseInsensitiveDict({}))

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
