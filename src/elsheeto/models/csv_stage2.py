"""Models for storing the result of stage 1 CSV sectioned CSV parsing.

Stage 2 is converting the stage 1 results into key/value and data payload header
sections.
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from elsheeto.models.common import ParsedSheetType


class HeaderRow(BaseModel):
    """Representation of a single row in a header section.

    Each row contains exactly a key and value (both strings).
    Empty fields are represented as empty strings.
    """

    #: First column (key)
    key: str
    #: Second column (value)
    value: str

    model_config = ConfigDict(frozen=True)

    @property
    def is_key_value_pair(self) -> bool:
        """Check if this row represents a non-empty key-value pair."""
        return bool(self.key.strip()) and bool(self.value.strip())

    @property
    def is_key_only(self) -> bool:
        """Check if this row has only a key (value is empty)."""
        return bool(self.key.strip()) and not bool(self.value.strip())

    @property
    def is_empty(self) -> bool:
        """Check if this row is completely empty."""
        return not bool(self.key.strip()) and not bool(self.value.strip())


class HeaderSection(BaseModel):
    """Representation of a header section in a stage 2 sample sheet."""

    #: Original section name (e.g., "header", "reads", "settings")
    name: str
    #: List of header rows preserving original structure
    rows: Annotated[list[HeaderRow], Field(default_factory=list)]

    model_config = ConfigDict(frozen=True)

    @property
    def key_values(self) -> dict[str, str]:
        """Get key-value pairs as a dictionary for backward compatibility."""
        result = {}
        for row in self.rows:
            if row.is_key_value_pair:
                result[row.key] = row.value
        return result


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
