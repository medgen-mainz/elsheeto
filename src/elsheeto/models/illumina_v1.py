"""Illumina sample sheet v1 specific models.

The Stage 2 results are converted into these models in Stage 3.
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class IlluminaHeader(BaseModel):
    """Representation of the Illumina v1 `Header` section."""

    #: Optional `Investigator Name` field.
    investigator_name: Annotated[str | None, Field(default=None)]
    #: Optional `Project Name` field.
    date: Annotated[str | None, Field(default=None)]
    #: Optional `Experiment Name` field.
    project_name: Annotated[str | None, Field(default=None)]
    #: Optional `Date` field.
    investigator_name: Annotated[str | None, Field(default=None)]
    #: Required `Workflow` field.
    workflow: Annotated[str, Field(default="GenerateFASTQ")]
    #: Optional `Assay` field.
    assay: Annotated[str | None, Field(default=None)]
    #: `Chemistry` field, must be set to `amplicon` (case insensitive)
    #: for dual indexing.
    chemistry: Annotated[str | None, Field(default=None)]

    #: Optional extra metadata.
    extra_metadata: Annotated[dict[str, str], Field(default_factory=dict)]

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
    data: dict[str, str]

    #: Optional extra metadata.
    extra_metadata: Annotated[dict[str, str], Field(default_factory=dict)]

    #: Model configuration.
    model_config = ConfigDict(frozen=True)


class IlluminaSample(BaseModel):
    """One entry in the Illumina v1 `Data` section."""

    #: Optional `Lane` field.
    lane: int | None = None
    #: `Sample_ID` field.
    sample_id: str
    #: Optional `Sample_Name` field.
    sample_plate: str | None = None
    #: Optional `Sample_Well` field.
    sample_well: str | None = None
    #: Optional `Index_Plate_Well` field.
    index_plate_well: str | None = None
    #: Optional `I7_Index_ID` field.
    i7_index_id: str | None = None
    #: `index` field.
    index: str
    #: Optional `I5_Index_ID` field.
    i5_index_id: str | None = None
    #: `index2` field.
    index2: str | None = None
    #: Optional `Sample_Project` field.
    sample_project: str | None = None
    #: Optional `Description` field.
    description: str | None = None

    #: List of header names in the sample sheet.
    header_names: Annotated[list[str], Field(default_factory=list)]
    #: Optional extra metadata.
    extra_metadata: Annotated[dict[str, str], Field(default_factory=dict)]

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
    data: list[IlluminaSample]

    #: Model configuration.
    model_config = ConfigDict(frozen=True)
