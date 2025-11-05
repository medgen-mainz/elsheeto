"""Aviti-specific CSV writer implementation."""

import io
from typing import TYPE_CHECKING

from elsheeto.writer.base import CsvWriter

if TYPE_CHECKING:
    from elsheeto.models.aviti import AvitiSheet


class AvitiCsvWriter(CsvWriter):
    """CSV writer for Aviti sample sheets.

    This writer handles the specific formatting requirements for Aviti sample sheets,
    including section ordering, lane-specific settings, and composite indices.
    """

    def write_to_string(self, sheet: "AvitiSheet") -> str:
        """Write an Aviti sample sheet to CSV string format.

        Args:
            sheet: The AvitiSheet to write.

        Returns:
            The CSV content as a string.
        """
        output = io.StringIO()
        writer = self._create_csv_writer(output)

        # Write RunValues section
        if sheet.run_values and sheet.run_values.data:
            self._write_run_values_section(writer, sheet)
            self._write_empty_line(writer)

        # Write Settings section
        if sheet.settings and sheet.settings.settings.entries:
            self._write_settings_section(writer, sheet)
            self._write_empty_line(writer)

        # Write Samples section
        self._write_samples_section(writer, sheet)

        return output.getvalue()

    def _write_run_values_section(self, writer, sheet: "AvitiSheet") -> None:
        """Write the RunValues section.

        Args:
            writer: The CSV writer object.
            sheet: The AvitiSheet containing the data.
        """
        self._write_section_header(writer, "RunValues")
        writer.writerow(["Keyname", "Value"])

        if sheet.run_values:
            for key, value in sheet.run_values.data.items():
                writer.writerow([key, value])

    def _write_settings_section(self, writer, sheet: "AvitiSheet") -> None:
        """Write the Settings section.

        Args:
            writer: The CSV writer object.
            sheet: The AvitiSheet containing the data.
        """
        self._write_section_header(writer, "Settings")

        if sheet.settings and sheet.settings.settings.entries:
            # Check if any settings have lane specifications
            has_lanes = any(entry.lane is not None for entry in sheet.settings.settings.entries)

            if has_lanes:
                # 3-column format with lanes, add extra trailing commas for compatibility
                writer.writerow(["SettingName", "Value", "Lane", "", ""])
                for entry in sheet.settings.settings.entries:
                    writer.writerow([entry.name, entry.value, entry.lane or "", "", ""])
            else:
                # 2-column format without lanes
                writer.writerow(["SettingName", "Value"])
                for entry in sheet.settings.settings.entries:
                    writer.writerow([entry.name, entry.value])
        else:  # pragma: no cover
            # Empty settings section
            writer.writerow(["SettingName", "Value"])

    def _write_samples_section(self, writer, sheet: "AvitiSheet") -> None:
        """Write the Samples section.

        Args:
            writer: The CSV writer object.
            sheet: The AvitiSheet containing the data.
        """
        self._write_section_header(writer, "Samples")

        if not sheet.samples:
            # Empty samples section with minimal headers
            writer.writerow(["SampleName", "Index1", "Index2"])
            return

        # Determine which columns are needed based on sample data
        headers = ["SampleName", "Index1", "Index2"]

        # Check if any samples have optional fields
        has_lane = any(sample.lane is not None for sample in sheet.samples)
        has_project = any(sample.project is not None for sample in sheet.samples)
        has_external_id = any(sample.external_id is not None for sample in sheet.samples)
        has_description = any(sample.description is not None for sample in sheet.samples)

        # Add optional headers if any sample uses them
        if has_lane:
            headers.append("Lane")
        if has_project:
            headers.append("Project")
        if has_external_id:
            headers.append("ExternalId")
        if has_description:
            headers.append("Description")

        # Check for extra metadata columns
        extra_columns = set()
        for sample in sheet.samples:
            extra_columns.update(sample.extra_metadata.keys())

        # Add extra columns in sorted order for consistency
        headers.extend(sorted(extra_columns))

        # Write the header row
        writer.writerow(headers)

        # Write sample data
        for sample in sheet.samples:
            row = [sample.sample_name, sample.index1, sample.index2 or ""]

            # Add optional fields if headers include them
            if has_lane:
                row.append(sample.lane or "")
            if has_project:
                row.append(sample.project or "")
            if has_external_id:
                row.append(sample.external_id or "")
            if has_description:
                row.append(sample.description or "")

            # Add extra metadata fields
            for col in sorted(extra_columns):
                row.append(sample.extra_metadata.get(col, ""))

            writer.writerow(row)
