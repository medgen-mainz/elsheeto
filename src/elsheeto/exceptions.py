class ElsheetoException(Exception):
    """Base exception for elsheeto."""


class RawCsvException(ElsheetoException):
    """Exception for errors related to raw CSV processing."""


class ElsheetoWarning(UserWarning):
    """Base warning for elsheeto."""


class LeadingSectionedCsvWarning(ElsheetoWarning):
    """Warning issued when there is leading content before the first header in
    a sectioned CSV file.
    """


class ColumnConsistencyWarning(ElsheetoWarning):
    """Warning issued when CSV rows have inconsistent column counts.

    This warning is issued when rows within a section have different numbers
    of columns. Missing cells are automatically padded with empty strings.
    """
