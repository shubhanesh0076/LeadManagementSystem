from rest_framework.exceptions import APIException
# custom_exceptions.py

class UnexpectedError(Exception):
    """Exception raised for an unexpected error in the application.

    Attributes:
        message -- explanation of the error
        original_exception -- the original exception that was raised
    """

    def __init__(self, message="An unexpected error occurred.", original_exception=None):
        self.message = message
        self.original_exception = original_exception
        super().__init__(self.message)

    def __str__(self):
        if self.original_exception:
            return f"UnexpectedError: {self.message} (Original exception: {self.original_exception})"
        return f"UnexpectedError: {self.message}"
    


class LeadAlreadyAttemptedException(APIException):
    status_code = 409
    default_detail = 'This lead has already been attempted by another user.'
    default_code = 'lead_already_attempted'
    

class PageNotFound(APIException):
    status_code = 404
    default_detail = 'Invalid page. Please select a valid page number.'
    default_code = 'lead_already_attempted'
