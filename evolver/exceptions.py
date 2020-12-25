class InvalidRegexError(Exception):
    """Raised when an invalid regex has been specified"""

    pass


class NotFoundError(Exception):
    """Raised when no valid regex match can be compiled"""

    pass
