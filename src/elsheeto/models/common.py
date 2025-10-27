from enum import Enum


class ParsedSheetType(str, Enum):
    """Resulting sheet type after raw CSV parsing in stage 1."""

    #: Sectionless.
    SECTIONLESS = "sectionless"
    #: Multi-section sheet.
    SECTIONED = "sectioned"
