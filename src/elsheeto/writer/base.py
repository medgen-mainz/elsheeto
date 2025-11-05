"""Base classes for CSV writing functionality."""

import csv
import io
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WriterConfiguration(BaseModel):
    """Configuration options for CSV writers.

    This class provides configuration options for controlling CSV output format,
    such as field ordering, empty line handling, and quotation preferences.
    """

    #: Whether to include empty lines between sections.
    include_empty_lines: bool = Field(default=True, description="Include empty lines between sections")

    #: CSV dialect settings.
    csv_dialect: str = Field(default="excel", description="CSV dialect to use")

    #: Quoting behavior for CSV fields.
    quoting: int = Field(default=csv.QUOTE_MINIMAL, description="CSV quoting behavior")

    #: Line terminator to use.
    lineterminator: str = Field(default="\n", description="Line terminator")

    model_config = ConfigDict(frozen=True)


class CsvWriter(ABC):
    """Abstract base class for CSV writers.

    This class provides the common interface and functionality for writing
    sample sheets to CSV format. Subclasses implement platform-specific
    formatting logic.
    """

    def __init__(self, config: WriterConfiguration | None = None) -> None:
        """Initialize the writer with configuration.

        Args:
            config: Writer configuration. If None, default configuration is used.
        """
        self.config = config or WriterConfiguration()

    @abstractmethod
    def write_to_string(self, sheet: Any) -> str:
        """Write a sample sheet to CSV string format.

        Args:
            sheet: The sample sheet object to write.

        Returns:
            The CSV content as a string.
        """
        raise NotImplementedError  # pragma: no cover

    def write_to_file(self, sheet: Any, file_path: str) -> None:
        """Write a sample sheet to a CSV file.

        Args:
            sheet: The sample sheet object to write.
            file_path: Path to the output CSV file.
        """
        csv_content = self.write_to_string(sheet)
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            f.write(csv_content)

    def _write_section_header(self, writer: Any, section_name: str) -> None:
        """Write a section header to the CSV.

        Args:
            writer: The CSV writer object.
            section_name: Name of the section (e.g., "RunValues", "Settings").
        """
        writer.writerow([f"[{section_name}]"])

    def _write_empty_line(self, writer: Any) -> None:
        """Write an empty line to the CSV if configured to do so.

        Args:
            writer: The CSV writer object.
        """
        if self.config.include_empty_lines:
            writer.writerow([])

    def _create_csv_writer(self, output: io.StringIO) -> Any:
        """Create a CSV writer with the configured dialect.

        Args:
            output: The string buffer to write to.

        Returns:
            A configured CSV writer.
        """
        return csv.writer(
            output,
            dialect=self.config.csv_dialect,
            quoting=self.config.quoting,  # type: ignore[arg-type]
            lineterminator=self.config.lineterminator,
        )
