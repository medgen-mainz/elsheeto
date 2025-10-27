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


class CaseConsistency(str, Enum):
    """Modes for handling upper/lower case in sections and headers/keys."""

    #: Case-sensitive mode.
    CASE_SENSITIVE = "case_sensitive"
    #: Case-insensitive mode.
    CASE_INSENSITIVE = "case_insensitive"

    def is_case_sensitive(self) -> bool:
        """Return whether the mode is case-sensitive."""
        return self == CaseConsistency.CASE_SENSITIVE


class ColumnConsistency(str, Enum):
    """Modes for handling inconsistent columns in CSV files."""

    #: Strict mode requiring consistent columns in each section.
    STRICT_SECTIONED = "strict_sectioned"
    #: Strict mode requiring consistent columns globally.
    STRICT_GLOBAL = "strict_global"
    #: Loose mode allowing variable columns.
    LOOSE = "loose"


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
    #: Case sensitivity configuration for section headers.
    section_header_case: CaseConsistency = CaseConsistency.CASE_INSENSITIVE
    #: Case sensitivity configuration for column headers.
    column_header_case: CaseConsistency = CaseConsistency.CASE_INSENSITIVE
    #: Case sensitivity for keys.
    key_case: CaseConsistency = CaseConsistency.CASE_INSENSITIVE
    #: Column consistency configuration.
    column_consistency: ColumnConsistency = ColumnConsistency.STRICT_SECTIONED

    model_config = ConfigDict(
        frozen=True,
    )
