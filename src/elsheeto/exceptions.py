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
