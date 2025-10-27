"""Aviti sample sheet (aka Sequencing Manifest) specific models.

The Stage 2 results are converted into these models in Stage 3.
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class AvitiSample(BaseModel):
    """Representation of a single Aviti sample."""

    #: Required value from `SampleName` column.
    sample_name: str
    #: Required value from `Index1` column.
    index1: str
    #: Required value from `Index2` column.
    index2: str
    #: Optional value from `Lane` column.
    lane: str | None = None
    #: Optional value from `Project` column.
    project: str | None = None
    #: Optional value from `ExternalId` column.
    external_id: str | None = None
    #: Optional value from `Description` column.
    description: str | None = None

    #: List of header names in the sample sheet.
    header_names: Annotated[list[str], Field(default_factory=list)]
    #: Optional extra metadata.
    extra_metadata: Annotated[dict[str, str], Field(default_factory=dict)]

    #: Model configuration.
    model_config = ConfigDict(frozen=True)


class AvitiRunValues(BaseModel):
    """Representation of the `RunValues` section of an Aviti sample sheet."""

    model_config = ConfigDict(
        frozen=True,
    )


class AvitiSetting(BaseModel):
    key: str
    value: str
    lane: str


class AvitiSettings(BaseModel):
    """Representation of the `Settings` section of an Aviti sample sheet."""

    model_config = ConfigDict(
        frozen=True,
    )


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
    SampleName, Index1, Index2,
    ```
    """

    #: The `RunValues` section.
    run_values: AvitiRunValues | None
    #: The `Settings` section.
    settings: AvitiSettings | None
    #: The `Samples` section.
    samples: list[AvitiSample]

    model_config = ConfigDict(
        frozen=True,
    )
