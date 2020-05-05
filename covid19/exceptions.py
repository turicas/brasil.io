class SpreadsheetValidationErrors(Exception):
    """
    Custom exception to hold all error messages raised when validating spreadsheets
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._error_messages = set()

    def new_error(self, msg):
        self._error_messages.add(msg)

    @property
    def error_messages(self):
        return list(self._error_messages)

    def raise_if_errors(self):
        if self.error_messages:
            raise self

    def __str__(self):
        return " - ".join(self.error_messages)


class OnlyOneSpreadsheetException(Exception):
    """
    Raised when checking if a spreadsheet is ready to be imported but there's no other
    one to compare with
    """
