"""Models for storing the result of stage 1 CSV sectioned CSV parsing.

Stage 1 is raw CSV parsing and splitting into sections.  Here, only
consistency checks of columns are made per-section or globally.
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from elsheeto.models.common import ParsedSheetType


class ParsedRawSection(BaseModel):
    """Representation of a parsed section in a sectioned CSV file."""

    #: Name of the section.
    name: str
    #: Number of columns in the section, 0 if there are no data rows.
    num_columns: int
    #: Data rows in the section.
    data: Annotated[list[list[str]], Field(default_factory=list)]

    model_config = ConfigDict(
        frozen=True,
    )


class ParsedRawSheet(BaseModel):
    """Representation of a parsed raw sectioned CSV file."""

    #: Delimiter used in the file.
    delimiter: str
    #: Resulting sheet type.
    sheet_type: ParsedSheetType

    #: Parsed sections in the sheet, a single one with `name` "" (empty string) if
    #: sectionless.
    sections: Annotated[list[ParsedRawSection], Field(default_factory=list)]

    model_config = ConfigDict(
        frozen=True,
    )
