"""Aviti sample sheet (aka Sequencing Manifest) specific models.

The Stage 2 results are converted into these models in Stage 3.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    extra_metadata: dict[str, str] = Field(default_factory=dict)

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
    data: dict[str, str] = Field(default_factory=dict)
    #: Optional extra metadata.
    extra_metadata: dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(frozen=True)


class AvitiSettings(BaseModel):
    """Representation of the `Settings` section of an Aviti sample sheet."""

    #: Key-value pairs from the Settings section.
    data: dict[str, str] = Field(default_factory=dict)
    #: Optional extra metadata.
    extra_metadata: dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(frozen=True)


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
