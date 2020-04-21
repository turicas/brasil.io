class SpreadsheetValidationErrors(Exception):
    """
    Custom exception to hold all error messages raised during the validation process
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_messages = []

    def new_error(self, msg):
        self.error_messages.append(msg)

    def raise_if_errors(self):
        if self.error_messages:
            raise self

    def __str__(self):
        return ' - '.join(self.error_messages)
