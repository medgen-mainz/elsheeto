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

        # Combine all header sections
        for section in parsed_sheet.header_sections:
            header_data.update(section.key_values)

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
        # Look for reads section in header sections (single-value rows)
        for section in parsed_sheet.header_sections:
            # Check if this looks like a reads section based on values
            if self._is_reads_section(section.key_values):
                read_lengths = []
                for _key, value in section.key_values.items():
                    try:
                        # Try to parse as integer (read length)
                        length = int(value.strip())
                        if length > 0:  # Valid read length
                            read_lengths.append(length)
                    except (ValueError, AttributeError):  # pragma: no cover
                        # Skip non-numeric values
                        continue

                if read_lengths:
                    return IlluminaReads(read_lengths=read_lengths)

        return None

    def _is_reads_section(self, key_values: dict[str, str]) -> bool:
        """Check if a section contains read length data.

        Args:
            key_values: The key-value pairs from the section.

        Returns:
            True if this appears to be a reads section.
        """
        # Check if most values are numeric (read lengths)
        numeric_count = 0
        total_count = len(key_values)

        if total_count == 0:
            return False

        # Only consider sections with purely numeric keys and values as reads sections
        for key, value in key_values.items():
            try:
                # Both key and value should be numeric for reads sections
                key_num = int(key.strip())
                value_num = int(value.strip())

                # Reasonable read length range (typically 25-500bp)
                if 25 <= key_num <= 500 and 25 <= value_num <= 500 and key_num == value_num:
                    numeric_count += 1
            except (ValueError, AttributeError):
                continue

        # If ALL values are valid read lengths, this is likely a reads section
        return numeric_count > 0 and numeric_count == total_count

    def _parse_settings(self, parsed_sheet: ParsedSheet) -> IlluminaSettings | None:
        """Parse settings section from structured data.

        Args:
            parsed_sheet: The structured parsed sheet.

        Returns:
            Parsed IlluminaSettings or None if no settings found.
        """
        # Settings are typically key-value pairs that aren't reads or header data
        settings_data = {}
        extra_metadata = {}

        for section in parsed_sheet.header_sections:
            # Skip sections that look like reads
            if self._is_reads_section(section.key_values):
                continue

            # For now, consider any remaining header sections as potential settings
            # In practice, we might need more sophisticated logic
            if len(section.key_values) > 0:
                # This is a heuristic - you might want to refine this
                contains_settings_keys = any(
                    key.lower().startswith(("setting", "config", "param")) for key in section.key_values.keys()
                )

                if contains_settings_keys:
                    settings_data.update(section.key_values)

        if settings_data:
            return IlluminaSettings(data=settings_data, extra_metadata=extra_metadata)

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


def parse(*, parsed_sheet: ParsedSheet, config: ParserConfiguration) -> IlluminaSampleSheet:
    """Convert structured sheet data into Illumina v1 sample sheet.

    Args:
        parsed_sheet: The structured parsed sheet from stage 2.
        config: Parser configuration to use.

    Returns:
        The validated Illumina v1 sample sheet.
    """
    parser = Parser(config)
    return parser.parse(parsed_sheet=parsed_sheet)
