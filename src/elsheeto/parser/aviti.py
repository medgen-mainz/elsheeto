"""Implementation of stage 3 parser for Aviti sample sheets.

Stage 3 converts the structured content from stage 2 into platform-specific
validated models. This module handles Aviti sample sheet format conversion.
"""

import logging

from pydantic import ValidationError

from elsheeto.models.aviti import (
    AvitiRunValues,
    AvitiSample,
    AvitiSettingEntries,
    AvitiSettingEntry,
    AvitiSettings,
    AvitiSheet,
)
from elsheeto.models.csv_stage2 import ParsedSheet
from elsheeto.models.utils import CaseInsensitiveDict
from elsheeto.parser.common import ParserConfiguration

#: The module logger.
LOGGER = logging.getLogger(__name__)


class Parser:
    """Stage 3 parser for Aviti sample sheets.

    Converts ParsedSheet (stage 2) into AvitiSheet by:
    - Mapping header sections to AvitiRunValues and AvitiSettings
    - Validating and converting data rows to AvitiSample objects
    - Handling composite indices in Index1/Index2 columns
    - Applying Aviti-specific validation rules
    """

    def __init__(self, config: ParserConfiguration) -> None:
        """Initialize the parser with the given configuration.

        Args:
            config: Parser configuration to use.
        """
        self.config = config

    def parse(self, *, parsed_sheet: ParsedSheet) -> AvitiSheet:
        """Convert structured sheet data into Aviti sample sheet.

        Args:
            parsed_sheet: The structured parsed sheet from stage 2.

        Returns:
            The validated Aviti sample sheet.

        Raises:
            ValueError: If the sheet cannot be converted to Aviti format.
            ValidationError: If the data doesn't meet Aviti requirements.
        """
        LOGGER.debug("Converting stage 2 sheet to Aviti sample sheet")

        # Parse different sections
        run_values = self._parse_run_values(parsed_sheet)
        settings = self._parse_settings(parsed_sheet)
        samples = self._parse_samples(parsed_sheet)

        # Create and validate the sample sheet
        try:
            aviti_sheet = AvitiSheet(
                run_values=run_values,
                settings=settings,
                samples=samples,
            )
            LOGGER.info("Successfully created Aviti sample sheet with %d samples", len(samples))
            return aviti_sheet
        except ValidationError as e:  # pragma: no cover
            LOGGER.error("Validation failed for Aviti sample sheet: %s", e)
            raise

    def _parse_run_values(self, parsed_sheet: ParsedSheet) -> AvitiRunValues | None:
        """Parse RunValues section from structured data.

        Args:
            parsed_sheet: The structured parsed sheet.

        Returns:
            Parsed AvitiRunValues or None if no RunValues section found.
        """
        # Find the "runvalues" section by name (case-insensitive)
        for section in parsed_sheet.header_sections:
            if section.name.lower() == "runvalues":
                return AvitiRunValues(
                    data=CaseInsensitiveDict(section.key_values), extra_metadata=CaseInsensitiveDict({})
                )

        return None

    def _parse_settings(self, parsed_sheet: ParsedSheet) -> AvitiSettings | None:
        """Parse Settings section from structured data.

        Args:
            parsed_sheet: The structured parsed sheet.

        Returns:
            Parsed AvitiSettings or None if no Settings section found.
        """

        # Find the "settings" section by name (case-insensitive)
        for section in parsed_sheet.header_sections:
            if section.name.lower() == "settings":
                settings = []
                extra_metadata = {}

                for row_idx, row in enumerate(section.rows):
                    # Filter out empty cells
                    non_empty_cells = [cell.strip() for cell in row if cell.strip()]

                    # Skip header rows (detect by checking if first few cells look like column names)
                    if (
                        row_idx == 0
                        and len(non_empty_cells) >= 2
                        and any(
                            header_name.lower() in non_empty_cells[0].lower()
                            for header_name in ["settingname", "setting", "name", "key"]
                        )
                        and any(header_name.lower() in non_empty_cells[1].lower() for header_name in ["value", "val"])
                    ):
                        LOGGER.debug("Skipping header row in settings section: %s", non_empty_cells)
                        continue

                    if len(non_empty_cells) == 2:
                        # Simple key-value pair
                        settings.append(AvitiSettingEntry(name=non_empty_cells[0], value=non_empty_cells[1], lane=None))
                    elif len(non_empty_cells) == 3:
                        # Lane-specific setting: SettingName, Value, Lane
                        settings.append(
                            AvitiSettingEntry(
                                name=non_empty_cells[0], value=non_empty_cells[1], lane=non_empty_cells[2]
                            )
                        )
                    elif len(non_empty_cells) > 3:  # pragma: no cover
                        # Error: Aviti settings should not have more than 3 columns
                        raise ValueError(
                            f"Invalid Aviti settings row: found {len(non_empty_cells)} non-empty fields, "
                            f"expected 2 (SettingName, Value) or 3 (SettingName, Value, Lane). "
                            f"Row content: {non_empty_cells}"
                        )
                    # Skip empty rows (len(non_empty_cells) == 0)

                return AvitiSettings(
                    settings=AvitiSettingEntries(entries=settings), extra_metadata=CaseInsensitiveDict(extra_metadata)
                )

        return None

    def _parse_samples(self, parsed_sheet: ParsedSheet) -> list[AvitiSample]:
        """Parse samples section into AvitiSample objects.

        Args:
            parsed_sheet: The structured parsed sheet.

        Returns:
            List of parsed AvitiSample objects.

        Raises:
            ValueError: If samples section is invalid or missing required fields.
        """
        data_section = parsed_sheet.data_section

        if not data_section.headers or not data_section.data:
            LOGGER.warning("No samples section found or samples section is empty")
            return []

        samples = []
        headers = data_section.headers

        # Field mapping from CSV headers to model fields (case-insensitive)
        field_mapping = {
            "samplename": "sample_name",
            "index1": "index1",
            "index2": "index2",
            "lane": "lane",
            "project": "project",
            "externalid": "external_id",
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

                    # Clean the value - handle index2 specially
                    clean_value = value.strip() if value else ""
                    if clean_value == "" and header_lower != "index2":
                        clean_value = None

                    # Map to known fields
                    if header_lower in field_mapping:
                        model_field = field_mapping[header_lower]
                        sample_data[model_field] = clean_value
                    else:
                        # Store unknown fields in extra metadata
                        if clean_value is not None and clean_value != "":
                            extra_metadata[header] = clean_value

                # Validate required fields
                if "sample_name" not in sample_data or not sample_data["sample_name"]:
                    raise ValueError(f"Missing required SampleName in row {row_idx + 1}")

                if "index1" not in sample_data or not sample_data["index1"]:
                    raise ValueError(f"Missing required Index1 in row {row_idx + 1}")

                # Ensure index2 is always present, even if empty
                if "index2" not in sample_data:
                    sample_data["index2"] = ""

                # Add extra metadata if any
                if extra_metadata:
                    sample_data["extra_metadata"] = extra_metadata

                # Create the sample
                sample = AvitiSample(**sample_data)
                samples.append(sample)

            except (ValidationError, ValueError) as e:
                LOGGER.error("Failed to parse sample in row %d: %s", row_idx + 1, e)
                raise ValueError(f"Invalid sample data in row {row_idx + 1}: {e}") from e

        LOGGER.debug("Successfully parsed %d samples", len(samples))
        return samples


def from_stage2(*, parsed_sheet: ParsedSheet, config: ParserConfiguration) -> AvitiSheet:
    """Convert structured sheet data into Aviti sample sheet.

    Args:
        parsed_sheet: The structured parsed sheet from stage 2.
        config: Parser configuration to use.

    Returns:
        The validated Aviti sample sheet.
    """
    parser = Parser(config)
    return parser.parse(parsed_sheet=parsed_sheet)
