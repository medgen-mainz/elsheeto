from elsheeto.parser.common import CsvDelimiter


def test_csv_delimiter():
    assert CsvDelimiter.AUTO.candidate_delimiters() == [",", "\t", ";"]
    assert CsvDelimiter.COMMA.candidate_delimiters() == [","]
    assert CsvDelimiter.TAB.candidate_delimiters() == ["\t"]
    assert CsvDelimiter.SEMICOLON.candidate_delimiters() == [";"]
