"""Illumina v1 CSV writer implementation."""

import io
from typing import TYPE_CHECKING

from elsheeto.writer.base import CsvWriter

if TYPE_CHECKING:
    from elsheeto.models.illumina_v1 import IlluminaSampleSheet


class IlluminaCsvWriter(CsvWriter):
    """CSV writer for Illumina v1 sample sheets.

    This writer handles the specific format requirements for Illumina v1 sample sheets,
    including proper section ordering, header field formatting, read lengths, and
    trailing commas for compatibility with existing parsers.
    """

    def write_to_string(self, sheet: "IlluminaSampleSheet") -> str:
        """Write an IlluminaSampleSheet to a CSV string.

        Args:
            sheet: The IlluminaSampleSheet to write.

        Returns:
            CSV representation of the sheet.
        """
        output = io.StringIO()
        writer = self._create_csv_writer(output)

        # Write sections in the correct order
        self._write_header_section(writer, sheet)
        self._write_reads_section(writer, sheet)
        self._write_settings_section(writer, sheet)
        self._write_data_section(writer, sheet)

        return output.getvalue()

    def _write_header_section(self, writer, sheet: "IlluminaSampleSheet") -> None:
        """Write the Header section.

        Args:
            writer: The CSV writer object.
            sheet: The IlluminaSampleSheet containing the data.
        """
        self._write_section_header(writer, "Header")

        # Define field mapping from snake_case to display names
        field_mapping = {
            "iem_file_version": "IEMFileVersion",
            "investigator_name": "Investigator Name",
            "experiment_name": "Experiment Name",
            "date": "Date",
            "workflow": "Workflow",
            "application": "Application",
            "instrument_type": "Instrument Type",
            "assay": "Assay",
            "index_adapters": "Index Adapters",
            "description": "Description",
            "chemistry": "Chemistry",
            "run": "Run",
        }

        # Write header fields (with trailing commas for compatibility)
        header_dict = sheet.header.model_dump(exclude={"extra_metadata"})
        for field_name, display_name in field_mapping.items():
            value = header_dict.get(field_name)
            if value is not None:
                # Add trailing commas to match Illumina format (10 commas total)
                writer.writerow([display_name, value] + [""] * 9)

        # Write extra metadata if any
        for key, value in sheet.header.extra_metadata.items():
            writer.writerow([key, value] + [""] * 9)

        # Add empty line after header
        if self.config.include_empty_lines:
            writer.writerow([""] * 11)

    def _write_reads_section(self, writer, sheet: "IlluminaSampleSheet") -> None:
        """Write the Reads section.

        Args:
            writer: The CSV writer object.
            sheet: The IlluminaSampleSheet containing the data.
        """
        self._write_section_header(writer, "Reads")

        if sheet.reads and sheet.reads.read_lengths:
            for read_length in sheet.reads.read_lengths:
                # Add trailing commas to match Illumina format
                writer.writerow([str(read_length)] + [""] * 10)

        # Add empty line after reads
        if self.config.include_empty_lines:
            writer.writerow([""] * 11)

    def _write_settings_section(self, writer, sheet: "IlluminaSampleSheet") -> None:
        """Write the Settings section.

        Args:
            writer: The CSV writer object.
            sheet: The IlluminaSampleSheet containing the data.
        """
        self._write_section_header(writer, "Settings")

        if sheet.settings and sheet.settings.data:
            for key, value in sheet.settings.data.items():
                # Add trailing commas to match Illumina format
                writer.writerow([key, value] + [""] * 9)

        # Add empty line after settings
        if self.config.include_empty_lines:
            writer.writerow([""] * 11)

    def _write_data_section(self, writer, sheet: "IlluminaSampleSheet") -> None:
        """Write the Data section.

        Args:
            writer: The CSV writer object.
            sheet: The IlluminaSampleSheet containing the data.
        """
        self._write_section_header(writer, "Data")

        if sheet.data:
            # Determine which fields are actually used
            all_fields = [
                "sample_id",
                "sample_name",
                "sample_plate",
                "sample_well",
                "index_plate_well",
                "i7_index_id",
                "index",
                "i5_index_id",
                "index2",
                "sample_project",
                "description",
            ]

            # Check for extra metadata fields across all samples
            extra_fields = set()
            for sample in sheet.data:
                extra_fields.update(sample.extra_metadata.keys())

            # Determine which standard fields have non-None values
            used_fields = []
            field_display_names = {
                "sample_id": "Sample_ID",
                "sample_name": "Sample_Name",
                "sample_plate": "Sample_Plate",
                "sample_well": "Sample_Well",
                "index_plate_well": "Index_Plate_Well",
                "i7_index_id": "I7_Index_ID",
                "index": "index",
                "i5_index_id": "I5_Index_ID",
                "index2": "index2",
                "sample_project": "Sample_Project",
                "description": "Description",
            }

            # Include lane if any sample has a lane
            has_lanes = any(sample.lane is not None for sample in sheet.data)
            if has_lanes:
                used_fields.append("lane")
                field_display_names["lane"] = "Lane"

            # Always include core fields, then add others that are used
            core_fields = ["sample_id"]  # Sample_ID is always required
            used_fields.extend(core_fields)

            for field in all_fields:
                if field not in used_fields and any(getattr(sample, field) is not None for sample in sheet.data):
                    used_fields.append(field)

            # Add extra metadata fields in sorted order
            for field in sorted(extra_fields):
                used_fields.append(field)
                field_display_names[field] = field

            # Write header row
            header_row = [field_display_names.get(field, field) for field in used_fields]
            writer.writerow(header_row)

            # Write sample data
            for sample in sheet.data:
                row = []
                sample_dict = sample.model_dump(exclude={"extra_metadata"})

                for field in used_fields:
                    if field in sample_dict:
                        value = sample_dict[field]
                        row.append(str(value) if value is not None else "")
                    elif field in sample.extra_metadata:
                        row.append(str(sample.extra_metadata[field]))
                    else:
                        row.append("")

                writer.writerow(row)

        # Add final empty line
        if self.config.include_empty_lines:
            writer.writerow([])

    def _write_section_header(self, writer, section_name: str) -> None:
        """Write a section header with trailing commas.

        Args:
            writer: The CSV writer object.
            section_name: Name of the section.
        """
        # Illumina format uses trailing commas for column alignment
        writer.writerow([f"[{section_name}]"] + [""] * 10)
