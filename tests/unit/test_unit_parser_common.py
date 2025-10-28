from elsheeto.parser.common import CaseConsistency, CsvDelimiter


def test_csv_delimiter():
    assert CsvDelimiter.AUTO.candidate_delimiters() == [",", "\t", ";"]
    assert CsvDelimiter.COMMA.candidate_delimiters() == [","]
    assert CsvDelimiter.TAB.candidate_delimiters() == ["\t"]
    assert CsvDelimiter.SEMICOLON.candidate_delimiters() == [";"]


def test_case_consistency():
    assert CaseConsistency.CASE_SENSITIVE.is_case_sensitive() is True
    assert CaseConsistency.CASE_INSENSITIVE.is_case_sensitive() is False
