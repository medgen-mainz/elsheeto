"""Implementation of stage 3 parser for Illumina v1 sample sheets.

Stage 3 converts the structured content from stage 2 into platform-specific
validated models. This module handles Illumina v1 sample sheet format conversion.
"""

import logging

from pydantic import ValidationError

from elsheeto.models.csv_stage2 import ParsedSheet
from elsheeto.models.illumina_v1 import (
    IlluminaHeader,
    IlluminaReads,
    IlluminaSample,
    IlluminaSampleSheet,
    IlluminaSettings,
)
from elsheeto.models.utils import CaseInsensitiveDict
from elsheeto.parser.common import ParserConfiguration

#: The module logger.
LOGGER = logging.getLogger(__name__)


class Parser:
    """Stage 3 parser for Illumina v1 sample sheets.

    Converts ParsedSheet (stage 2) into IlluminaSampleSheet by:
    - Mapping header sections to IlluminaHeader
    - Converting reads data to IlluminaReads
    - Parsing settings into IlluminaSettings
    - Validating and converting data rows to IlluminaSample objects
    - Applying Illumina v1 specific validation rules
    """

    def __init__(self, config: ParserConfiguration) -> None:
        """Initialize the parser with the given configuration.

        Args:
            config: Parser configuration to use.
        """
        self.config = config

    def parse(self, *, parsed_sheet: ParsedSheet) -> IlluminaSampleSheet:
        """Convert structured sheet data into Illumina v1 sample sheet.

        Args:
            parsed_sheet: The structured parsed sheet from stage 2.

        Returns:
            The validated Illumina v1 sample sheet.

        Raises:
            ValueError: If the sheet cannot be converted to Illumina v1 format.
            ValidationError: If the data doesn't meet Illumina v1 requirements.
        """
        LOGGER.debug("Converting stage 2 sheet to Illumina v1 sample sheet")

        # Parse different sections
        header = self._parse_header(parsed_sheet)
        reads = self._parse_reads(parsed_sheet)
        settings = self._parse_settings(parsed_sheet)
        data = self._parse_data(parsed_sheet)

        # Create and validate the sample sheet
        try:
            sample_sheet = IlluminaSampleSheet(
                header=header,
                reads=reads,
                settings=settings,
                data=data,
            )
            LOGGER.info("Successfully created Illumina v1 sample sheet with %d samples", len(data))
            return sample_sheet
        except ValidationError as e:  # pragma: no cover
            LOGGER.error("Validation failed for Illumina v1 sample sheet: %s", e)
            raise

    def _parse_header(self, parsed_sheet: ParsedSheet) -> IlluminaHeader:
        """Parse header section from structured data.

        Args:
            parsed_sheet: The structured parsed sheet.

        Returns:
            Parsed IlluminaHeader.
        """
        header_data = {}
        extra_metadata = {}

        # Find the "header" section by name
        header_section = None
        for section in parsed_sheet.header_sections:
            if section.name == "header":
                header_section = section
                break

        if not header_section:
            # If no header section found, create minimal header
            LOGGER.warning("No header section found, creating minimal header")
            return IlluminaHeader(
                iem_file_version=None,
                investigator_name=None,
                experiment_name=None,
                date=None,
                workflow="GenerateFASTQ",
                application=None,
                instrument_type=None,
                assay=None,
                index_adapters=None,
                description=None,
                chemistry=None,
                run=None,
                extra_metadata=CaseInsensitiveDict({}),
            )

        # Extract key-value pairs from header section
        for row in header_section.rows:
            # Filter out empty cells
            non_empty_cells = [cell.strip() for cell in row if cell.strip()]
            # Only treat rows with exactly 2 non-empty cells as key-value pairs
            if len(non_empty_cells) == 2:
                header_data[non_empty_cells[0]] = non_empty_cells[1]

        # Map known fields with case-insensitive matching
        field_mapping = {
            "iemfileversion": "iem_file_version",
            "investigator name": "investigator_name",
            "experiment name": "experiment_name",
            "date": "date",
            "workflow": "workflow",
            "application": "application",
            "instrument type": "instrument_type",
            "assay": "assay",
            "index adapters": "index_adapters",
            "description": "description",
            "chemistry": "chemistry",
            "run": "run",
        }

        mapped_data = {}
        for key, value in header_data.items():
            key_lower = key.lower()
            if key_lower in field_mapping:
                mapped_data[field_mapping[key_lower]] = value
            else:
                extra_metadata[key] = value

        # Add extra metadata if any
        if extra_metadata:
            mapped_data["extra_metadata"] = extra_metadata

        return IlluminaHeader(**mapped_data)

    def _parse_reads(self, parsed_sheet: ParsedSheet) -> IlluminaReads | None:
        """Parse reads section from structured data.

        Args:
            parsed_sheet: The structured parsed sheet.

        Returns:
            Parsed IlluminaReads or None if no reads section found.
        """
        # Find the "reads" section by name
        reads_section = None
        for section in parsed_sheet.header_sections:
            if section.name == "reads":
                reads_section = section
                break

        if not reads_section:
            return None

        read_lengths = []
        for row in reads_section.rows:
            try:
                # Filter out empty cells
                non_empty_cells = [cell.strip() for cell in row if cell.strip()]

                if len(non_empty_cells) == 1:
                    # Handle format like "151" (single read length value)
                    length = int(non_empty_cells[0])
                    if 1 <= length <= 1000:  # Reasonable read length range (including UMI)
                        read_lengths.append(length)
                elif len(non_empty_cells) > 1:
                    # Invalid row in reads section - reads should only contain single values
                    LOGGER.warning(
                        "Invalid row in reads section: found %d values: %s", len(non_empty_cells), non_empty_cells
                    )
                    return None
                # Empty rows (len(non_empty_cells) == 0) are ignored
            except (ValueError, AttributeError):
                LOGGER.warning("Could not parse read length from row: %s", row)
                return None

        if read_lengths:
            return IlluminaReads(read_lengths=read_lengths)

        return None

    def _parse_settings(self, parsed_sheet: ParsedSheet) -> IlluminaSettings | None:
        """Parse settings section from structured data.

        Args:
            parsed_sheet: The structured parsed sheet.

        Returns:
            Parsed IlluminaSettings or None if no settings found.
        """
        # Settings section is ignored per requirements
        return None

    def _parse_data(self, parsed_sheet: ParsedSheet) -> list[IlluminaSample]:
        """Parse data section into IlluminaSample objects.

        Args:
            parsed_sheet: The structured parsed sheet.

        Returns:
            List of parsed IlluminaSample objects.

        Raises:
            ValueError: If data section is invalid or missing required fields.
        """
        data_section = parsed_sheet.data_section

        if not data_section.headers or not data_section.data:
            LOGGER.warning("No data section found or data section is empty")
            return []

        samples = []
        headers = data_section.headers

        # Create header mapping for case-insensitive lookup
        {header.lower(): header for header in headers}

        # Field mapping from CSV headers to model fields
        field_mapping = {
            "lane": "lane",
            "sample_id": "sample_id",
            "sample_name": "sample_name",
            "sample_plate": "sample_plate",
            "sample_well": "sample_well",
            "index_plate_well": "index_plate_well",
            "inline_id": "inline_id",
            "i7_index_id": "i7_index_id",
            "index": "index",
            "i5_index_id": "i5_index_id",
            "index2": "index2",
            "sample_project": "sample_project",
            "description": "description",
        }

        for row_idx, row in enumerate(data_section.data):
            try:
                sample_data = {}
                extra_metadata = {}

                # Map row data to sample fields
                for col_idx, value in enumerate(row):
                    if col_idx >= len(headers):
                        break

                    header = headers[col_idx]
                    header_lower = header.lower()

                    # Clean the value
                    clean_value = value.strip() if value else None
                    if clean_value == "":
                        clean_value = None

                    # Map to known fields
                    if header_lower in field_mapping:
                        model_field = field_mapping[header_lower]

                        # Special handling for integer fields
                        if model_field == "lane" and clean_value is not None:
                            try:
                                sample_data[model_field] = int(clean_value)
                            except ValueError:
                                LOGGER.warning("Invalid lane value '%s' in row %d, skipping", clean_value, row_idx + 1)
                                sample_data[model_field] = None
                        else:
                            sample_data[model_field] = clean_value
                    else:
                        # Store unknown fields in extra metadata
                        if clean_value is not None:
                            extra_metadata[header] = clean_value

                # Ensure required fields are present
                if "sample_id" not in sample_data or not sample_data["sample_id"]:
                    raise ValueError(f"Missing required Sample_ID in row {row_idx + 1}")

                # Add extra metadata if any
                if extra_metadata:
                    sample_data["extra_metadata"] = extra_metadata

                # Create the sample
                sample = IlluminaSample(**sample_data)
                samples.append(sample)

            except (ValidationError, ValueError) as e:
                LOGGER.error("Failed to parse sample in row %d: %s", row_idx + 1, e)
                raise ValueError(f"Invalid sample data in row {row_idx + 1}: {e}") from e

        LOGGER.debug("Successfully parsed %d samples", len(samples))
        return samples


def from_stage2(*, parsed_sheet: ParsedSheet, config: ParserConfiguration) -> IlluminaSampleSheet:
    """Convert structured sheet data into Illumina v1 sample sheet.

    Args:
        parsed_sheet: The structured parsed sheet from stage 2.
        config: Parser configuration to use.

    Returns:
        The validated Illumina v1 sample sheet.
    """
    parser = Parser(config)
    return parser.parse(parsed_sheet=parsed_sheet)
