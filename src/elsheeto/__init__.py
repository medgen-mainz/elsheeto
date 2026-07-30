"""Elsheeto is a Python library for parsing and handling Illumina v1 and Aviti
sample sheets.
"""

from elsheeto.facade import (
    parse_aviti,
    parse_aviti_from_data,
    parse_illumina_v1,
    parse_illumina_v1_from_data,
    write_aviti_to_file,
    write_aviti_to_string,
    write_illumina_v1_to_file,
    write_illumina_v1_to_string,
)
from elsheeto.models.utils import CaseInsensitiveDict
from elsheeto.parser.common import (
    ColumnConsistency,
    CsvDelimiter,
    ParserConfiguration,
)
from elsheeto.version import __version__
from elsheeto.writer.base import WriterConfiguration

__all__ = [
    "__version__",
    "parse_aviti",
    "parse_aviti_from_data",
    "parse_illumina_v1",
    "parse_illumina_v1_from_data",
    "write_aviti_to_file",
    "write_aviti_to_string",
    "write_illumina_v1_to_file",
    "write_illumina_v1_to_string",
    "ParserConfiguration",
    "WriterConfiguration",
    "CaseInsensitiveDict",
    "ColumnConsistency",
    "CsvDelimiter",
]
