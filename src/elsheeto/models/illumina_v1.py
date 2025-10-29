"""Illumina sample sheet v1 specific models.

The Stage 2 results are converted into these models in Stage 3.
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from elsheeto.models.utils import CaseInsensitiveDict


class IlluminaHeader(BaseModel):
    """Representation of the Illumina v1 `Header` section."""

    #: Optional `IEMFileVersion` field.
    iem_file_version: Annotated[str | None, Field(default=None)]
    #: Optional `Investigator Name` field.
    investigator_name: Annotated[str | None, Field(default=None)]
    #: Optional `Experiment Name` field.
    experiment_name: Annotated[str | None, Field(default=None)]
    #: Optional `Date` field.
    date: Annotated[str | None, Field(default=None)]
    #: Required `Workflow` field.
    workflow: Annotated[str, Field(default="GenerateFASTQ")]
    #: Optional `Application` field.
    application: Annotated[str | None, Field(default=None)]
    #: Optional `Instrument Type` field.
    instrument_type: Annotated[str | None, Field(default=None)]
    #: Optional `Assay` field.
    assay: Annotated[str | None, Field(default=None)]
    #: Optional `Index Adapters` field.
    index_adapters: Annotated[str | None, Field(default=None)]
    #: Optional `Description` field.
    description: Annotated[str | None, Field(default=None)]
    #: `Chemistry` field, must be set to `amplicon` (case insensitive)
    #: for dual indexing.
    chemistry: Annotated[str | None, Field(default=None)]
    #: Optional `Run` field.
    run: Annotated[str | None, Field(default=None)]

    #: Optional extra metadata for fields not explicitly defined.
    extra_metadata: Annotated[CaseInsensitiveDict, Field(default_factory=lambda: CaseInsensitiveDict({}))]

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
    extra_metadata: Annotated[CaseInsensitiveDict, Field(default_factory=lambda: CaseInsensitiveDict({}))]

    #: Model configuration.
    model_config = ConfigDict(frozen=True)


class IlluminaSample(BaseModel):
    """One entry in the Illumina v1 `Data` section."""

    #: Optional `Lane` field.
    lane: Annotated[int | None, Field(default=None)]
    #: `Sample_ID` field.
    sample_id: str
    #: Optional `Sample_Name` field.
    sample_name: Annotated[str | None, Field(default=None)]
    #: Optional `Sample_Plate` field.
    sample_plate: Annotated[str | None, Field(default=None)]
    #: Optional `Sample_Well` field.
    sample_well: Annotated[str | None, Field(default=None)]
    #: Optional `Index_Plate_Well` field.
    index_plate_well: Annotated[str | None, Field(default=None)]
    #: Optional `Inline_ID` field.
    inline_id: Annotated[str | None, Field(default=None)]
    #: Optional `I7_Index_ID` field.
    i7_index_id: Annotated[str | None, Field(default=None)]
    #: `index` field.
    index: Annotated[str | None, Field(default=None)]
    #: Optional `I5_Index_ID` field.
    i5_index_id: Annotated[str | None, Field(default=None)]
    #: `index2` field.
    index2: Annotated[str | None, Field(default=None)]
    #: Optional `Sample_Project` field.
    sample_project: Annotated[str | None, Field(default=None)]
    #: Optional `Description` field.
    description: Annotated[str | None, Field(default=None)]

    #: Optional extra metadata for fields not explicitly defined.
    extra_metadata: Annotated[CaseInsensitiveDict, Field(default_factory=lambda: CaseInsensitiveDict({}))]

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
