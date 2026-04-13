"""Domain exceptions for the OMS backend.

These exceptions are raised by service layer code and caught/translated
to HTTP responses in the API layer, keeping services free of HTTP concerns.
"""


class OMSBaseException(Exception):
    """Base exception for all OMS domain errors."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class OrderValidationError(OMSBaseException):
    """Raised when order data fails validation."""
    pass


class TransitionError(OMSBaseException):
    """Raised when a workflow state transition is invalid."""
    pass


class ApplicationNotFoundError(OMSBaseException):
    """Raised when a referenced application does not exist."""
    pass


class ProcessingDisabledError(OMSBaseException):
    """Raised when order processing is globally disabled."""
    pass
