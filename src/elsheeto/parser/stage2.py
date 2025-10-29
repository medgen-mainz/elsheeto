"""Implementation of stage 2 parser.

Stage 2 converts the raw sectioned data from stage 1 into structured content:
- Key-value sections (Header, Settings, etc.) become HeaderSection objects
- Tabular sections (Data, Samples, etc.) become DataSection objects

The parser determines section types based on content structure and known patterns.
"""

import logging

from elsheeto.models.csv_stage1 import ParsedRawSection, ParsedRawSheet
from elsheeto.models.csv_stage2 import DataSection, HeaderSection, ParsedSheet
from elsheeto.parser.common import ParserConfiguration

#: The module logger.
LOGGER = logging.getLogger(__name__)

#: Known data section names (case-insensitive)
DATA_SECTION_NAMES = {"data", "samples"}


class Parser:
    """Stage 2 parser that converts raw sectioned data into structured content.

    Converts ParsedRawSheet (stage 1) into ParsedSheet (stage 2) by:
    - Identifying section types (key-value vs tabular)
    - Converting key-value sections to HeaderSection objects
    - Converting tabular sections to DataSection objects
    - Applying configuration-based transformations
    """

    def __init__(self, config: ParserConfiguration) -> None:
        """Initialize the parser with the given configuration.

        Args:
            config: Parser configuration to use.
        """
        self.config = config

    def parse(self, *, raw_sheet: ParsedRawSheet) -> ParsedSheet:
        """Convert raw sectioned data into structured content.

        Args:
            raw_sheet: The raw parsed sheet from stage 1.

        Returns:
            The structured parsed sheet.
        """
        LOGGER.debug("Converting stage 1 raw sheet to stage 2 structured content")

        header_sections = []
        data_section = None

        for section in raw_sheet.sections:
            if self._is_data_section(section):
                if data_section is not None:
                    LOGGER.warning("Multiple data sections found, using the last one")
                data_section = self._convert_to_data_section(section)
            else:
                header_section = self._convert_to_header_section(section)
                if header_section:  # Only add non-empty header sections
                    header_sections.append(header_section)

        # If no data section was found, create an empty one
        if data_section is None:
            data_section = DataSection(headers=[], header_to_index={}, data=[])
            LOGGER.debug("No data section found, created empty data section")

        return ParsedSheet(
            delimiter=raw_sheet.delimiter,
            sheet_type=raw_sheet.sheet_type,
            header_sections=header_sections,
            data_section=data_section,
        )

    def _is_data_section(self, section: ParsedRawSection) -> bool:
        """Determine if a section should be treated as a data section.

        Args:
            section: The section to analyze.

        Returns:
            True if this should be treated as a data section.
        """
        # Check if section name matches known data section names (case-insensitive comparison)
        if section.name.lower() in DATA_SECTION_NAMES:
            return True

        # For sectionless sheets, treat the unnamed section as data if it has tabular structure
        if section.name == "" and self._has_tabular_structure(section):
            return True

        # Check if section has tabular structure (header row + data rows)
        if self._has_tabular_structure(section):
            return True

        return False

    def _has_tabular_structure(self, section: ParsedRawSection) -> bool:
        """Check if a section has tabular structure (headers + consistent data rows).

        Args:
            section: The section to analyze.

        Returns:
            True if the section appears to have tabular structure.
        """
        if not section.data or len(section.data) < 2:
            return False

        # Check if we have at least one potential header row and data rows
        # First row should have text-like headers, subsequent rows should be consistent
        first_row = section.data[0]

        # Headers should be non-empty strings
        if not all(cell.strip() for cell in first_row):
            return False

        # Check if subsequent rows have similar structure (similar column count)
        expected_cols = len(first_row)
        for row in section.data[1:]:
            # Allow some flexibility in column count for real-world data
            if abs(len(row) - expected_cols) > 1:
                return False

        # Additional heuristic: if this looks like key-value pairs, it's not tabular
        # Key-value pairs typically have exactly 2 columns and the first column
        # contains descriptive keys rather than simple identifiers
        # Single-column sections are typically not tabular data
        if expected_cols == 1:
            return False

        if expected_cols == 2 and len(section.data) <= 10:  # Arbitrary threshold
            # Check if first column looks like keys (longer descriptive text)
            first_col_values = [row[0].strip() for row in section.data if row]

            # Check for common key patterns indicating key-value pairs:
            # 1. Keys that are more descriptive (contain non-alphanumeric chars, longer length)
            # 2. Pattern where first column contains varied text types
            # 3. Values in second column are not obviously column data

            # Look for descriptive key patterns
            has_descriptive_keys = any(
                " " in key and len(key) > 8 for key in first_col_values  # Contains space and is reasonably long
            )

            # Look for key naming patterns (camelCase, snake_case, etc.)
            has_key_patterns = any(
                "_" in key or (key != key.lower() and key != key.upper() and not key.istitle())
                for key in first_col_values
            )

            # Check if keys look like configuration/metadata keys
            metadata_patterns = ["version", "name", "date", "type", "setting", "config", "param"]
            has_metadata_keys = any(
                any(pattern in key.lower() for pattern in metadata_patterns) for key in first_col_values
            )

            if has_descriptive_keys or has_key_patterns or has_metadata_keys:
                return False

        return True

    def _convert_to_header_section(self, section: ParsedRawSection) -> HeaderSection | None:
        """Convert a raw section to a header section (preserving original row structure).

        Args:
            section: The raw section to convert.

        Returns:
            HeaderSection object or None if section is empty.
        """
        rows = []

        for row in section.data:
            if not row or all(cell.strip() == "" for cell in row):
                continue  # Skip empty rows

            # Simply preserve the row as-is (no more validation on number of fields)
            rows.append(row)

        return HeaderSection(name=section.name.lower(), rows=rows) if rows else None

    def _convert_to_data_section(self, section: ParsedRawSection) -> DataSection:
        """Convert a raw section to a data section (tabular data).

        Args:
            section: The raw section to convert.

        Returns:
            DataSection object.
        """
        if not section.data:
            return DataSection(headers=[], header_to_index={}, data=[])

        # First row is typically headers
        headers = []
        data_rows = []

        if section.data:
            # Extract headers from first row
            header_row = section.data[0]
            headers = [cell.strip() for cell in header_row]

            # Remaining rows are data
            data_rows = section.data[1:]

        # Create header to index mapping
        header_to_index = {header: idx for idx, header in enumerate(headers)}

        return DataSection(
            headers=headers,
            header_to_index=header_to_index,
            data=data_rows,
        )


def from_stage1(*, raw_sheet: ParsedRawSheet, config: ParserConfiguration) -> ParsedSheet:
    """Convert raw sectioned data into structured content.

    Args:
        raw_sheet: The raw parsed sheet from stage 1.
        config: Parser configuration to use.

    Returns:
        The structured parsed sheet.
    """
    parser = Parser(config)
    return parser.parse(raw_sheet=raw_sheet)
