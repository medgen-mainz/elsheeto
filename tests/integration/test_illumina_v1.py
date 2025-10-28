"""Integration tests for Illumina v1 read length parsing with different CSV formats."""

from pathlib import Path

import pytest

import elsheeto.parser.illumina_v1 as stage3
import elsheeto.parser.stage1 as stage1
import elsheeto.parser.stage2 as stage2
from elsheeto.parser.common import ParserConfiguration


class TestIlluminaV1ReadLengthFormats:
    """Integration tests for different Illumina v1 read length CSV formats."""

    def test_reads_format_with_trailing_commas(self):
        """Test parsing reads section with trailing commas: [Reads],,\\n151,,\\n151,,"""
        config = ParserConfiguration()

        # CSV content with trailing commas
        csv_content = """[Header],,
IEMFileVersion,4,,
Experiment Name,Read Format Test,,
Date,2025-10-28,,
Workflow,GenerateFASTQ,,
[Reads],,
151,,
151,,
[Data],,
Sample_ID,Sample_Name,Sample_Project
Sample1,Test Sample 1,Project1"""

        # Stage 1: Parse raw CSV
        raw_sheet = stage1.from_csv(data=csv_content, config=config)
        assert raw_sheet is not None

        # Stage 2: Convert to structured format
        structured_sheet = stage2.from_stage1(raw_sheet=raw_sheet, config=config)
        assert structured_sheet is not None

        # Stage 3: Convert to Illumina v1 specific format
        illumina_sheet = stage3.from_stage2(parsed_sheet=structured_sheet, config=config)

        # Verify reads parsing
        assert illumina_sheet.reads is not None
        assert illumina_sheet.reads.read_lengths == [151, 151]

    def test_reads_format_without_trailing_commas(self):
        """Test parsing reads section without trailing commas: [Reads]\\n151\\n151"""
        config = ParserConfiguration()

        # CSV content without trailing commas
        csv_content = """[Header]
IEMFileVersion,4
Experiment Name,Read Format Test
Date,2025-10-28
Workflow,GenerateFASTQ
[Reads]
151
151
[Data]
Sample_ID,Sample_Name,Sample_Project
Sample1,Test Sample 1,Project1"""

        # Stage 1: Parse raw CSV
        raw_sheet = stage1.from_csv(data=csv_content, config=config)
        assert raw_sheet is not None

        # Stage 2: Convert to structured format
        structured_sheet = stage2.from_stage1(raw_sheet=raw_sheet, config=config)
        assert structured_sheet is not None

        # Stage 3: Convert to Illumina v1 specific format
        illumina_sheet = stage3.from_stage2(parsed_sheet=structured_sheet, config=config)

        # Verify reads parsing
        assert illumina_sheet.reads is not None
        assert illumina_sheet.reads.read_lengths == [151, 151]

    def test_reads_format_section_header_with_commas(self):
        """Test parsing reads section with commas in header: [Reads],\\n151,\\n151,"""
        config = ParserConfiguration()

        # CSV content with comma in section header
        csv_content = """[Header],
IEMFileVersion,4
Experiment Name,Read Format Test
Date,2025-10-28
Workflow,GenerateFASTQ
[Reads],
151,
151,
[Data],
Sample_ID,Sample_Name,Sample_Project
Sample1,Test Sample 1,Project1"""

        # Stage 1: Parse raw CSV
        raw_sheet = stage1.from_csv(data=csv_content, config=config)
        assert raw_sheet is not None

        # Stage 2: Convert to structured format
        structured_sheet = stage2.from_stage1(raw_sheet=raw_sheet, config=config)
        assert structured_sheet is not None

        # Stage 3: Convert to Illumina v1 specific format
        illumina_sheet = stage3.from_stage2(parsed_sheet=structured_sheet, config=config)

        # Verify reads parsing
        assert illumina_sheet.reads is not None
        assert illumina_sheet.reads.read_lengths == [151, 151]

    def test_reads_format_single_read(self):
        """Test parsing reads section with single read length."""
        config = ParserConfiguration()

        # CSV content with single read
        csv_content = """[Header]
IEMFileVersion,4
Experiment Name,Single Read Test
Date,2025-10-28
Workflow,GenerateFASTQ
[Reads]
75
[Data]
Sample_ID,Sample_Name,Sample_Project
Sample1,Test Sample 1,Project1"""

        # Stage 1: Parse raw CSV
        raw_sheet = stage1.from_csv(data=csv_content, config=config)
        assert raw_sheet is not None

        # Stage 2: Convert to structured format
        structured_sheet = stage2.from_stage1(raw_sheet=raw_sheet, config=config)
        assert structured_sheet is not None

        # Stage 3: Convert to Illumina v1 specific format
        illumina_sheet = stage3.from_stage2(parsed_sheet=structured_sheet, config=config)

        # Verify reads parsing
        assert illumina_sheet.reads is not None
        assert illumina_sheet.reads.read_lengths == [75]

    def test_reads_format_mixed_read_lengths(self):
        """Test parsing reads section with different read lengths."""
        config = ParserConfiguration()

        # CSV content with mixed read lengths (like UMI + reads)
        csv_content = """[Header],,
IEMFileVersion,4,,
Experiment Name,Mixed Read Test,,
Date,2025-10-28,,
Workflow,GenerateFASTQ,,
[Reads],,
150,,
8,,
130,,
[Data],,
Sample_ID,Sample_Name,Sample_Project
Sample1,Test Sample 1,Project1"""

        # Stage 1: Parse raw CSV
        raw_sheet = stage1.from_csv(data=csv_content, config=config)
        assert raw_sheet is not None

        # Stage 2: Convert to structured format
        structured_sheet = stage2.from_stage1(raw_sheet=raw_sheet, config=config)
        assert structured_sheet is not None

        # Stage 3: Convert to Illumina v1 specific format
        illumina_sheet = stage3.from_stage2(parsed_sheet=structured_sheet, config=config)

        # Verify reads parsing
        assert illumina_sheet.reads is not None
        assert illumina_sheet.reads.read_lengths == [150, 8, 130]

    def test_reads_format_empty_reads_section(self):
        """Test parsing when reads section is empty."""
        config = ParserConfiguration()

        # CSV content with empty reads section
        csv_content = """[Header]
IEMFileVersion,4
Experiment Name,No Reads Test
Date,2025-10-28
Workflow,GenerateFASTQ
[Reads]
[Data]
Sample_ID,Sample_Name,Sample_Project
Sample1,Test Sample 1,Project1"""

        # Stage 1: Parse raw CSV
        raw_sheet = stage1.from_csv(data=csv_content, config=config)
        assert raw_sheet is not None

        # Stage 2: Convert to structured format
        structured_sheet = stage2.from_stage1(raw_sheet=raw_sheet, config=config)
        assert structured_sheet is not None

        # Stage 3: Convert to Illumina v1 specific format
        illumina_sheet = stage3.from_stage2(parsed_sheet=structured_sheet, config=config)

        # Verify no reads section
        assert illumina_sheet.reads is None

    def test_reads_format_no_reads_section(self):
        """Test parsing when no reads section is present at all."""
        config = ParserConfiguration()

        # CSV content without reads section
        csv_content = """[Header]
IEMFileVersion,4
Experiment Name,No Reads Section Test
Date,2025-10-28
Workflow,GenerateFASTQ
[Data]
Sample_ID,Sample_Name,Sample_Project
Sample1,Test Sample 1,Project1"""

        # Stage 1: Parse raw CSV
        raw_sheet = stage1.from_csv(data=csv_content, config=config)
        assert raw_sheet is not None

        # Stage 2: Convert to structured format
        structured_sheet = stage2.from_stage1(raw_sheet=raw_sheet, config=config)
        assert structured_sheet is not None

        # Stage 3: Convert to Illumina v1 specific format
        illumina_sheet = stage3.from_stage2(parsed_sheet=structured_sheet, config=config)

        # Verify no reads section
        assert illumina_sheet.reads is None

    @pytest.mark.parametrize(
        "illumina_file,expected_reads",
        [
            ("illumina_v1/reads_format1.csv", [151, 151]),
            ("illumina_v1/reads_format2.csv", [151, 151]),
            ("illumina_v1/example1.csv", [149, 149]),
            ("illumina_v1/example2.csv", [150, 8, 130]),
        ],
    )
    def test_reads_parsing_from_files(self, illumina_file: str, expected_reads: list[int]):
        """Test read length parsing from actual test data files.

        This test verifies that different CSV formatting styles for reads sections
        are parsed correctly through the complete end-to-end pipeline.
        """
        config = ParserConfiguration()
        path_data = Path(__file__).parent.parent / "data"
        file_path = path_data / illumina_file

        # Stage 1: Parse raw CSV
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        raw_sheet = stage1.from_csv(data=content, config=config)
        assert raw_sheet is not None

        # Stage 2: Convert to structured format
        structured_sheet = stage2.from_stage1(raw_sheet=raw_sheet, config=config)
        assert structured_sheet is not None

        # Stage 3: Convert to Illumina v1 specific format
        illumina_sheet = stage3.from_stage2(parsed_sheet=structured_sheet, config=config)
        assert illumina_sheet is not None

        # Verify reads parsing matches expected
        if expected_reads:
            assert illumina_sheet.reads is not None
            assert illumina_sheet.reads.read_lengths == expected_reads
        else:
            assert illumina_sheet.reads is None

    def test_reads_format_with_extra_whitespace(self):
        """Test parsing reads section with extra whitespace around values."""
        config = ParserConfiguration()

        # CSV content with whitespace around values
        csv_content = """[Header]
IEMFileVersion,4
Experiment Name,Whitespace Test
[Reads]
 151
 151
[Data]
Sample_ID,Sample_Name
Sample1,Test Sample 1"""

        # Stage 1: Parse raw CSV
        raw_sheet = stage1.from_csv(data=csv_content, config=config)
        assert raw_sheet is not None

        # Stage 2: Convert to structured format
        structured_sheet = stage2.from_stage1(raw_sheet=raw_sheet, config=config)
        assert structured_sheet is not None

        # Stage 3: Convert to Illumina v1 specific format
        illumina_sheet = stage3.from_stage2(parsed_sheet=structured_sheet, config=config)

        # Verify reads parsing handles whitespace correctly
        assert illumina_sheet.reads is not None
        assert illumina_sheet.reads.read_lengths == [151, 151]

    def test_reads_format_with_invalid_values(self):
        """Test parsing reads section with invalid (non-numeric) values."""
        config = ParserConfiguration()

        # CSV content with invalid read values
        csv_content = """[Header]
IEMFileVersion,4
Experiment Name,Invalid Reads Test
[Reads]
151
abc
151
[Data]
Sample_ID,Sample_Name
Sample1,Test Sample 1"""

        # Stage 1: Parse raw CSV
        raw_sheet = stage1.from_csv(data=csv_content, config=config)
        assert raw_sheet is not None

        # Stage 2: Convert to structured format
        structured_sheet = stage2.from_stage1(raw_sheet=raw_sheet, config=config)
        assert structured_sheet is not None

        # Stage 3: Convert to Illumina v1 specific format
        illumina_sheet = stage3.from_stage2(parsed_sheet=structured_sheet, config=config)

        # Should not identify this as a reads section due to invalid values
        # The section should be treated as regular header data
        assert illumina_sheet.reads is None


class TestIlluminaV1EndToEndPipeline:
    """End-to-end integration tests for Illumina v1 sample sheet parsing."""

    @pytest.mark.parametrize(
        "illumina_file",
        [
            "illumina_v1/example1.csv",
            "illumina_v1/example2.csv",
        ],
    )
    def test_end_to_end_pipeline(self, illumina_file: str):
        """Test complete end-to-end parsing pipeline with real data files.

        This test verifies that stage 1 -> stage 2 -> stage 3 parsing works
        correctly with real Illumina v1 sample sheet files.
        """
        from elsheeto.models.illumina_v1 import IlluminaSampleSheet

        config = ParserConfiguration()
        path_data = Path(__file__).parent.parent / "data"
        file_path = path_data / illumina_file

        # Stage 1: Parse raw CSV
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        raw_sheet = stage1.from_csv(data=content, config=config)
        assert raw_sheet is not None

        # Stage 2: Convert to structured format
        structured_sheet = stage2.from_stage1(raw_sheet=raw_sheet, config=config)
        assert structured_sheet is not None
        assert len(structured_sheet.header_sections) > 0
        assert structured_sheet.data_section is not None

        # Stage 3: Convert to Illumina v1 specific format
        illumina_sheet = stage3.from_stage2(parsed_sheet=structured_sheet, config=config)
        assert illumina_sheet is not None
        assert isinstance(illumina_sheet, IlluminaSampleSheet)

        # Verify basic structure
        assert illumina_sheet.header is not None
        assert illumina_sheet.header.iem_file_version is not None
        assert illumina_sheet.data is not None
        assert len(illumina_sheet.data) > 0

        # Verify all samples have required fields
        for sample in illumina_sheet.data:
            assert sample.sample_id is not None and sample.sample_id.strip() != ""
