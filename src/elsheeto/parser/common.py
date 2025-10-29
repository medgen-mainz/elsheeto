"""Shared models / value objects for CSV parsing configuration."""

from enum import Enum

from pydantic import BaseModel, ConfigDict


class CsvDelimiter(str, Enum):
    """Enumeration of common CSV delimiters."""

    #: Auto-detect
    AUTO = "auto"
    #: Comma (,)
    COMMA = "comma"
    #: Tab (\t)
    TAB = "tab"
    #: Semicolon (;)
    SEMICOLON = "semicolon"

    def candidate_delimiters(self) -> list[str]:
        """Return candidate delimiters for the given enum value."""
        match self:
            case CsvDelimiter.AUTO:
                return [",", "\t", ";"]
            case CsvDelimiter.COMMA:
                return [","]
            case CsvDelimiter.TAB:
                return ["\t"]
            case CsvDelimiter.SEMICOLON:
                return [";"]


class ColumnConsistency(str, Enum):
    """Modes for handling inconsistent columns in CSV files."""

    #: Strict mode requiring consistent columns in each section.
    STRICT_SECTIONED = "strict_sectioned"
    #: Strict mode requiring consistent columns globally.
    STRICT_GLOBAL = "strict_global"
    #: Loose mode allowing variable columns.
    LOOSE = "loose"
    #: Pad missing cells silently without warnings.
    PAD = "pad"
    #: Warning mode - pad missing cells and issue warnings.
    WARN_AND_PAD = "warn_and_pad"


class ParserConfiguration(BaseModel):
    """Configuration for a generic (sectioned) CSV parser.

    Allows for configuring common parameters used when parsing CSV-like files
    that are sectioned as common for sequencing sample sheets.
    """

    #: Delimiter used in the CSV file, or auto-detect.
    delimiter: CsvDelimiter = CsvDelimiter.AUTO
    #: Whether section headers are required.
    require_section_headers: bool = True
    #: Whether to ignore empty lines.
    ignore_empty_lines: bool = True
    #: Line prefixes to recognize as comments.
    comment_prefixes: list[str] = ["#"]
    #: Column consistency configuration.
    column_consistency: ColumnConsistency = ColumnConsistency.WARN_AND_PAD

    model_config = ConfigDict(
        frozen=True,
    )
