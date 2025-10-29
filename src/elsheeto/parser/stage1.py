"""Implementation of stage 1 parser.

Here, we parse the sectioned CSV files.  This is done as follows.

- The file is first line-by-line, performing splitting at section headings.
- Each section is then interpreted as CSV and converted into `ParsedRawSection`
  objects.  Depending on the parser configuration, the column delimiter is
  guessed globally and column counts are enforced either per-section or globally.
"""

import csv
import io
import logging
import warnings

from elsheeto.exceptions import ColumnConsistencyWarning
from elsheeto.models.common import ParsedSheetType
from elsheeto.models.csv_stage1 import ParsedRawSection, ParsedRawSheet
from elsheeto.parser.common import (
    ColumnConsistency,
    ParserConfiguration,
)

#: The module logger.
LOGGER = logging.getLogger(__name__)


class Parser:
    """Splitter for sectioned CSV files.

    - Run CSV sniffer on the data to determine the delimiter.
    - Split the data into sections based on section headers.
    - Run global or per-section column consistency checks.
    - Return a `ParsedRawSheet` object.
    """

    def __init__(self, config: ParserConfiguration) -> None:
        """Initialize the splitter with the given configuration."""
        self.config = config

    def parse(self, *, data: str) -> ParsedRawSheet:
        """Parse the given sectioned CSV data into a ParsedRawSheet.

        Args:
            data: The sectioned CSV data as a string.

        Returns:
            The parsed raw sheet containing sections and metadata.
        """
        dialect = self._sniff_dialect(data=data)
        data_io = io.StringIO(data)

        reader = csv.reader(data_io, dialect=dialect)

        # Parse all rows and split into sections
        sections = self._parse_sections(reader)

        # Determine sheet type
        sheet_type = (
            ParsedSheetType.SECTIONED
            if len(sections) > 1 or (len(sections) == 1 and sections[0].name != "")
            else ParsedSheetType.SECTIONLESS
        )

        # Apply column consistency checks and potentially pad data
        sections = self._validate_column_consistency(sections)

        return ParsedRawSheet(delimiter=dialect.delimiter, sheet_type=sheet_type, sections=sections)

    def _sniff_dialect(self, *, data: str) -> type[csv.Dialect]:
        """Sniff CSV dialect from the data with fallback handling.

        Args:
            data: The CSV data to analyze.

        Returns:
            A CSV dialect class.
        """
        LOGGER.debug("Sniffing CSV dialect...")

        # First, try to sniff from the full data
        try:
            dialect = csv.Sniffer().sniff(sample=data, delimiters="".join(self.config.delimiter.candidate_delimiters()))
            self._log_dialect(dialect)
            return dialect
        except csv.Error:
            LOGGER.debug("Failed to sniff dialect from full data, trying data rows only...")

        # If that fails, try to extract data rows (non-section headers) and sniff from those
        try:
            data_rows = self._extract_data_rows_for_sniffing(data)
            if data_rows:
                dialect = csv.Sniffer().sniff(
                    sample=data_rows, delimiters="".join(self.config.delimiter.candidate_delimiters())
                )
                self._log_dialect(dialect)
                return dialect
        except csv.Error:
            LOGGER.debug("Failed to sniff dialect from data rows, using fallback...")

        # Fall back to a default dialect based on configuration
        fallback_delimiter = self._get_fallback_delimiter()
        LOGGER.info("Using fallback delimiter: '%s'", fallback_delimiter)

        # Create a custom dialect class
        class FallbackDialect(csv.excel):
            delimiter = fallback_delimiter

        return FallbackDialect

    def _extract_data_rows_for_sniffing(self, data: str) -> str:
        """Extract non-section header rows for dialect sniffing.

        Args:
            data: The full CSV data.

        Returns:
            Data rows without section headers for sniffing.
        """
        lines = data.split("\n")
        data_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):  # Skip comments
                continue
            if line.startswith("[") and line.endswith("]"):  # Skip section headers
                continue
            data_lines.append(line)

        return "\n".join(data_lines)

    def _get_fallback_delimiter(self) -> str:
        """Get the fallback delimiter based on configuration.

        Returns:
            The fallback delimiter to use.
        """
        candidates = self.config.delimiter.candidate_delimiters()
        return candidates[0] if candidates else ","

    def _log_dialect(self, dialect) -> None:
        """Log the detected CSV dialect.

        Args:
            dialect: The detected CSV dialect.
        """
        dialect_dict = {
            "delimiter": dialect.delimiter,
            "quotechar": dialect.quotechar,
            "escapechar": dialect.escapechar,
            "doublequote": dialect.doublequote,
            "skipinitialspace": dialect.skipinitialspace,
            "lineterminator": dialect.lineterminator,
        }
        LOGGER.info("Detected CSV dialect: %s", dialect_dict)

    def _parse_sections(self, reader) -> list[ParsedRawSection]:
        """Parse CSV rows into sections based on section headers.

        Args:
            reader: CSV reader for the data.

        Returns:
            List of parsed sections.
        """
        sections: list[ParsedRawSection] = []
        current_section_name = ""
        current_section_data: list[list[str]] = []

        for row in reader:
            # Skip empty lines if configured
            if self.config.ignore_empty_lines and self._is_empty_row(row):
                continue

            # Skip comment lines
            if self._is_comment_row(row):
                continue

            # Check if this is a section header
            section_name = self._extract_section_name(row)
            if section_name is not None:
                # Save previous section if it exists
                if current_section_name or current_section_data:
                    sections.append(self._create_section(current_section_name, current_section_data))

                # Start new section
                current_section_name = section_name
                current_section_data = []
            else:
                # Add row to current section
                current_section_data.append(row)

        # Add final section
        if current_section_name or current_section_data:
            sections.append(self._create_section(current_section_name, current_section_data))

        # If no sections were found and we require section headers, create a sectionless sheet
        if not sections:
            sections.append(ParsedRawSection(name="", num_columns=0, data=[]))

        return sections

    def _is_empty_row(self, row: list[str]) -> bool:
        """Check if a row is empty (all cells are empty strings)."""
        return all(cell.strip() == "" for cell in row)

    def _is_comment_row(self, row: list[str]) -> bool:
        """Check if a row is a comment based on configured prefixes."""
        if not row:
            return False
        first_cell = row[0].strip()
        return any(first_cell.startswith(prefix) for prefix in self.config.comment_prefixes)

    def _extract_section_name(self, row: list[str]) -> str | None:
        """Extract section name from a row if it's a section header.

        Section headers are expected to be in the format [SectionName].

        Args:
            row: The CSV row to check.

        Returns:
            Section name if this is a section header, None otherwise.
        """
        if not row or not row[0].strip():
            return None

        first_cell = row[0].strip()
        if first_cell.startswith("[") and first_cell.endswith("]"):
            section_name = first_cell[1:-1]
            return section_name

        return None

    def _create_section(self, name: str, data: list[list[str]]) -> ParsedRawSection:
        """Create a ParsedRawSection from name and data."""
        num_columns = max(len(row) for row in data) if data else 0
        return ParsedRawSection(name=name, num_columns=num_columns, data=data)

    def _validate_column_consistency(self, sections: list[ParsedRawSection]) -> list[ParsedRawSection]:
        """Validate column consistency based on configuration.

        For WARN_AND_PAD mode, pads rows with missing cells and issues warnings.

        Args:
            sections: List of parsed sections to validate and potentially modify.

        Returns:
            List of sections, potentially with modified data for WARN_AND_PAD mode.

        Raises:
            ValueError: If column consistency requirements are not met (strict modes only).
        """
        if self.config.column_consistency == ColumnConsistency.LOOSE:
            return sections

        if self.config.column_consistency == ColumnConsistency.STRICT_GLOBAL:
            # Check that all sections have the same number of columns
            if sections:
                expected_columns = sections[0].num_columns
                for section in sections[1:]:
                    if section.num_columns != expected_columns:
                        raise ValueError(
                            f"Global column consistency violated: section '{section.name}' "
                            f"has {section.num_columns} columns, expected {expected_columns}"
                        )
            return sections

        elif self.config.column_consistency == ColumnConsistency.STRICT_SECTIONED:
            # Check that each section has consistent columns within itself
            for section in sections:
                self._validate_strict_sectioned_consistency(section)
            return sections

        elif self.config.column_consistency == ColumnConsistency.PAD:
            # Pad rows silently without warnings
            return [self._pad_section(section) for section in sections]

        elif self.config.column_consistency == ColumnConsistency.WARN_AND_PAD:
            # Pad rows and issue warnings for inconsistent columns
            return [self._warn_and_pad_section(section) for section in sections]

        raise AssertionError("unreachable")  # pragma: no cover

    def _validate_strict_sectioned_consistency(self, section: ParsedRawSection) -> None:
        """Validate strict sectioned consistency for a single section.

        Args:
            section: The section to validate.

        Raises:
            ValueError: If column consistency requirements are not met.
        """
        if section.data:
            # Find the first non-empty row to determine expected column count
            expected_columns = None
            for row in section.data:
                if row and any(cell.strip() for cell in row):  # Non-empty row
                    expected_columns = len(row)
                    break

            if expected_columns is None:  # pragma: no cover
                return  # All rows are empty, no consistency to check

            for i, row in enumerate(section.data):
                # Always skip truly empty rows in consistency check,
                # regardless of ignore_empty_lines setting
                if self._is_empty_row(row):
                    continue
                if len(row) != expected_columns:
                    raise ValueError(
                        f"Section '{section.name}' column consistency violated: "
                        f"row {i} has {len(row)} columns, expected {expected_columns}"
                    )

    def _pad_section(self, section: ParsedRawSection) -> ParsedRawSection:
        """Pad rows to consistent length silently without warnings.

        Args:
            section: The section to process and potentially modify.

        Returns:
            A new ParsedRawSection with padded data.
        """
        if not section.data:
            return section

        # Find the maximum column count in the section
        max_columns = 0
        for row in section.data:
            if not self._is_empty_row(row):
                max_columns = max(max_columns, len(row))

        if max_columns == 0:
            return section  # All rows are empty

        # Create new data with padded rows
        new_data = []

        for _i, row in enumerate(section.data):
            if self._is_empty_row(row):
                new_data.append(row)  # Keep empty rows as-is
                continue

            if len(row) < max_columns:
                # Pad the row with empty strings (no warning)
                new_data.append(row + [""] * (max_columns - len(row)))
            else:
                new_data.append(row)

        # Return new section with padded data and updated column count
        return ParsedRawSection(name=section.name, num_columns=max_columns, data=new_data)

    def _warn_and_pad_section(self, section: ParsedRawSection) -> ParsedRawSection:
        """Pad rows to consistent length and issue warnings for inconsistencies.

        Args:
            section: The section to process and potentially modify.

        Returns:
            A new ParsedRawSection with padded data.
        """
        if not section.data:
            return section

        # Find the maximum column count in the section
        max_columns = 0
        for row in section.data:
            if not self._is_empty_row(row):
                max_columns = max(max_columns, len(row))

        if max_columns == 0:
            return section  # All rows are empty

        # Create new data with padded rows
        new_data = []
        warnings_issued = False

        for _i, row in enumerate(section.data):
            if self._is_empty_row(row):
                new_data.append(row)  # Keep empty rows as-is
                continue

            if len(row) < max_columns:
                # Issue warning for missing columns
                if not warnings_issued:  # Only warn once per section to avoid spam
                    warnings.warn(
                        f"Section '{section.name}': padding missing cells with empty strings "
                        f"(some rows have fewer than {max_columns} columns)",
                        ColumnConsistencyWarning,
                        stacklevel=4,
                    )
                    warnings_issued = True
                # Pad the row with empty strings
                new_data.append(row + [""] * (max_columns - len(row)))
            else:
                new_data.append(row)

        # Return new section with padded data and updated column count
        return ParsedRawSection(name=section.name, num_columns=max_columns, data=new_data)


def from_csv(*, data: str, config: ParserConfiguration) -> ParsedRawSheet:
    """Parse the given sectioned CSV data.

    Args:
        data: The sectioned CSV data as a string.

    Returns:
        The parsed raw sheet.
    """
    parser = Parser(config)
    return parser.parse(data=data)
