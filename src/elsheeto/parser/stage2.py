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

        if not raw_sheet.sections:
            # No sections at all - create empty data section
            data_section = DataSection(headers=[], header_to_index={}, data=[])
            LOGGER.debug("No sections found, created empty data section")
        elif len(raw_sheet.sections) == 1 and raw_sheet.sections[0].name == "":
            # Sectionless sheet - single unnamed section is the data section
            data_section = self._convert_to_data_section(raw_sheet.sections[0])
            LOGGER.debug("Sectionless sheet: unnamed section treated as data section")
        else:
            # Sectioned sheet - last section is data, all others are headers
            # Process all sections except the last one as header sections
            for section in raw_sheet.sections[:-1]:
                header_section = self._convert_to_header_section(section)
                if header_section:  # Only add non-empty header sections
                    header_sections.append(header_section)

            # Last section is always the data section
            if raw_sheet.sections:
                data_section = self._convert_to_data_section(raw_sheet.sections[-1])
                LOGGER.debug("Sectioned sheet: last section treated as data section")

        # Ensure we always have a data section
        if data_section is None:
            data_section = DataSection(headers=[], header_to_index={}, data=[])
            LOGGER.debug("No data section created, using empty data section")

        return ParsedSheet(
            delimiter=raw_sheet.delimiter,
            sheet_type=raw_sheet.sheet_type,
            header_sections=header_sections,
            data_section=data_section,
        )

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
