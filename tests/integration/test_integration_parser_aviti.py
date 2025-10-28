"""Integration tests for Aviti sample sheet end-to-end parsing."""

from pathlib import Path

import pytest

import elsheeto.parser.aviti as stage3
import elsheeto.parser.stage1 as stage1
import elsheeto.parser.stage2 as stage2
from elsheeto.models.aviti import AvitiSheet
from elsheeto.parser.common import ParserConfiguration


class TestAvitiEndToEndPipeline:
    """End-to-end integration tests for Aviti sample sheet parsing."""

    @pytest.mark.parametrize(
        "aviti_file",
        [
            "aviti/example1.csv",
            "aviti/example2.csv",
            "aviti/example3.csv",
        ],
    )
    def test_end_to_end_pipeline(self, aviti_file: str):
        """Test complete end-to-end parsing pipeline with real data files.

        This test verifies that stage 1 -> stage 2 -> stage 3 parsing works
        correctly with real Aviti sample sheet files.
        """
        config = ParserConfiguration()
        path_data = Path(__file__).parent.parent / "data"
        file_path = path_data / aviti_file

        # Stage 1: Parse raw CSV
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        raw_sheet = stage1.from_csv(data=content, config=config)
        assert raw_sheet is not None

        # Stage 2: Convert to structured format
        structured_sheet = stage2.from_stage1(raw_sheet=raw_sheet, config=config)
        assert structured_sheet is not None
        assert structured_sheet.data_section is not None

        # Stage 3: Convert to Aviti specific format
        aviti_sheet = stage3.from_stage2(parsed_sheet=structured_sheet, config=config)
        assert aviti_sheet is not None
        assert isinstance(aviti_sheet, AvitiSheet)

        # Verify basic structure
        assert aviti_sheet.samples is not None
        assert len(aviti_sheet.samples) > 0

        # Verify all samples have required fields
        for sample in aviti_sheet.samples:
            assert sample.sample_name is not None and sample.sample_name.strip() != ""
            assert sample.index1 is not None
