"""Unit tests for facade functions."""

from pathlib import Path

from elsheeto.facade import (
    parse_aviti,
    parse_aviti_from_data,
    parse_illumina_v1,
    parse_illumina_v1_from_data,
)
from elsheeto.models.aviti import AvitiSheet
from elsheeto.models.illumina_v1 import IlluminaSampleSheet
from elsheeto.parser.common import ParserConfiguration


class TestIlluminaV1Facade:
    """Test Illumina v1 facade functions."""

    def test_parse_illumina_v1_from_data(self):
        """Test parsing Illumina v1 sample sheet from data."""
        data_path = Path(__file__).parent.parent / "data" / "illumina_v1" / "example1.csv"
        with open(data_path, "r", encoding="utf-8") as f:
            data = f.read()

        result = parse_illumina_v1_from_data(data)

        assert isinstance(result, IlluminaSampleSheet)
        assert result.header is not None
        assert len(result.data) > 0

    def test_parse_illumina_v1_from_data_with_config(self):
        """Test parsing Illumina v1 sample sheet from data with config."""
        data_path = Path(__file__).parent.parent / "data" / "illumina_v1" / "example1.csv"
        with open(data_path, "r", encoding="utf-8") as f:
            data = f.read()

        config = ParserConfiguration()
        result = parse_illumina_v1_from_data(data, config=config)

        assert isinstance(result, IlluminaSampleSheet)
        assert result.header is not None
        assert len(result.data) > 0

    def test_parse_illumina_v1_from_file(self):
        """Test parsing Illumina v1 sample sheet from file path."""
        data_path = Path(__file__).parent.parent / "data" / "illumina_v1" / "example1.csv"

        result = parse_illumina_v1(str(data_path))

        assert isinstance(result, IlluminaSampleSheet)
        assert result.header is not None
        assert len(result.data) > 0

    def test_parse_illumina_v1_from_file_with_config(self):
        """Test parsing Illumina v1 sample sheet from file path with config."""
        data_path = Path(__file__).parent.parent / "data" / "illumina_v1" / "example1.csv"

        config = ParserConfiguration()
        result = parse_illumina_v1(str(data_path), config=config)

        assert isinstance(result, IlluminaSampleSheet)
        assert result.header is not None
        assert len(result.data) > 0


class TestAvitiFacade:
    """Test Aviti facade functions."""

    def test_parse_aviti_from_data(self):
        """Test parsing Aviti sample sheet from data."""
        data_path = Path(__file__).parent.parent / "data" / "aviti" / "example1.csv"
        with open(data_path, "r", encoding="utf-8") as f:
            data = f.read()

        result = parse_aviti_from_data(data)

        assert isinstance(result, AvitiSheet)
        assert len(result.samples) > 0

    def test_parse_aviti_from_data_with_config(self):
        """Test parsing Aviti sample sheet from data with config."""
        data_path = Path(__file__).parent.parent / "data" / "aviti" / "example1.csv"
        with open(data_path, "r", encoding="utf-8") as f:
            data = f.read()

        config = ParserConfiguration()
        result = parse_aviti_from_data(data, config=config)

        assert isinstance(result, AvitiSheet)
        assert len(result.samples) > 0

    def test_parse_aviti_from_file(self):
        """Test parsing Aviti sample sheet from file path."""
        data_path = Path(__file__).parent.parent / "data" / "aviti" / "example1.csv"

        result = parse_aviti(str(data_path))

        assert isinstance(result, AvitiSheet)
        assert len(result.samples) > 0

    def test_parse_aviti_from_file_with_config(self):
        """Test parsing Aviti sample sheet from file path with config."""
        data_path = Path(__file__).parent.parent / "data" / "aviti" / "example1.csv"

        config = ParserConfiguration()
        result = parse_aviti(str(data_path), config=config)

        assert isinstance(result, AvitiSheet)
        assert len(result.samples) > 0
