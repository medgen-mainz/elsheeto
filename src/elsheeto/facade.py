"""Convenience facade functions for parsing sample sheets."""

from pathlib import Path

from elsheeto.models.aviti import AvitiSheet
from elsheeto.models.illumina_v1 import IlluminaSampleSheet
from elsheeto.parser.aviti import from_stage2 as aviti_from_stage2
from elsheeto.parser.common import ParserConfiguration
from elsheeto.parser.illumina_v1 import from_stage2 as illumina_v1_from_stage2
from elsheeto.parser.stage1 import from_csv as stage1_from_csv
from elsheeto.parser.stage2 import from_stage1 as stage2_from_stage1


def _csv_data_to_stage2(data: str, config: ParserConfiguration):
    """Convert CSV data to stage 2 ParsedSheet.

    Args:
        data: The CSV data as a string.
        config: Parser configuration.

    Returns:
        A ParsedSheet object representing the structured content.
    """
    raw_sheet = stage1_from_csv(data=data, config=config)
    parsed_sheet = stage2_from_stage1(raw_sheet=raw_sheet, config=config)
    return parsed_sheet


def parse_illumina_v1_from_data(data: str, config: ParserConfiguration | None = None) -> IlluminaSampleSheet:
    """Parse an Illumina v1 sample sheet from the given CSV data.

    This is a convenience function that runs all parsing stages internally.

    Args:
        data: The CSV data as a string.
        config: Optional parser configuration.

    Returns:
        An IlluminaSampleSheet object representing the parsed sample sheet.
    """
    if config is None:
        config = ParserConfiguration()

    parsed_sheet = _csv_data_to_stage2(data=data, config=config)
    illumina_v1_sheet = illumina_v1_from_stage2(parsed_sheet=parsed_sheet, config=config)
    return illumina_v1_sheet


def parse_illumina_v1(path: str | Path, config: ParserConfiguration | None = None) -> IlluminaSampleSheet:
    """Parse an Illumina v1 sample sheet from the given file path.

    This is a convenience function that runs all parsing stages internally.

    Args:
        path: The file path to the Illumina v1 sample sheet CSV file.
        config: Optional parser configuration.

    Returns:
        An IlluminaSampleSheet object representing the parsed sample sheet.
    """
    if config is None:
        config = ParserConfiguration()

    # Read the CSV file
    with open(path, "r") as f:
        data = f.read()

    return parse_illumina_v1_from_data(data=data, config=config)


def parse_aviti_from_data(data: str, config: ParserConfiguration | None = None) -> AvitiSheet:
    """Parse an Aviti sample sheet from the given CSV data.

    This is a convenience function that runs all parsing stages internally.

    Args:
        data: The CSV data as a string.
        config: Optional parser configuration.

    Returns:
        An AvitiSheet object representing the parsed sample sheet.
    """
    if config is None:
        config = ParserConfiguration()

    parsed_sheet = _csv_data_to_stage2(data=data, config=config)
    aviti_sheet = aviti_from_stage2(parsed_sheet=parsed_sheet, config=config)
    return aviti_sheet


def parse_aviti(path: str | Path, config: ParserConfiguration | None = None) -> AvitiSheet:
    """Parse an Aviti sample sheet from the given file path.

    This is a convenience function that runs all parsing stages internally.

    Args:
        path: The file path to the Aviti sample sheet CSV file.
        config: Optional parser configuration.

    Returns:
        An AvitiSheet object representing the parsed sample sheet.
    """
    if config is None:
        config = ParserConfiguration()

    # Read the CSV file
    with open(path, "r") as f:
        data = f.read()

    return parse_aviti_from_data(data=data, config=config)
