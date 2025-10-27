"""Models for storing the result of stage 1 CSV sectioned CSV parsing.

Stage 2 is converting the stage 1 results into key/value and data payload header
sections.
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from elsheeto.models.common import ParsedSheetType


class HeaderSection(BaseModel):
    """Representation of a key/value header section in a stage 2 sample sheet."""

    #: Mapping from keys to values.
    key_values: Annotated[dict[str, str], Field(default_factory=dict)]

    model_config = ConfigDict(
        frozen=True,
    )


class DataSection(BaseModel):
    """Representation of the data section in a stage 2 sample sheet."""

    #: Header names.
    headers: Annotated[list[str], Field(default_factory=list)]
    #: Header to index map.
    header_to_index: Annotated[dict[str, int], Field(default_factory=dict)]
    #: Data rows.
    data: Annotated[list[list[str]], Field(default_factory=list)]

    model_config = ConfigDict(
        frozen=True,
    )


class ParsedSheet(BaseModel):
    """Representation of a stage 2 sample sheet."""

    #: Delimiter used in the file.
    delimiter: str
    #: Resulting sheet type.
    sheet_type: ParsedSheetType

    #: Zero or more key/value header sections in the sheet.
    header_sections: Annotated[list[HeaderSection], Field(default_factory=list)]
    #: Single data section in the sheet.
    data_section: DataSection

    model_config = ConfigDict(
        frozen=True,
    )
