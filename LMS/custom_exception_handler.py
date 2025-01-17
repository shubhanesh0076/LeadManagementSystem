from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError, NotAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from utilities import utils
import json
from rest_framework.exceptions import ErrorDetail
from LMS.settings import DEFAULT_AUTO_FIELD



def _flatten_validation_errors(errors):
    """
    Flatten nested validation errors to extract the first error message per field.
    """
    flattened_errors = {}
    for field, error_list in errors.items():
        if isinstance(error_list, list) and len(error_list) > 0:
            flattened_errors[field] = error_list[0]
    return flattened_errors


def custom_exception_handler(exc, context):

    # Call DRF's default exception handler first
    response = exception_handler(exc, context)

    # Now add the custom payload to the response
    if response is not None:
        request = context.get("request")
        extra_information = {}
        try:
            # print("Message: ", exc.detail)
            if isinstance(exc, ValidationError):    
                
                if isinstance(exc.detail, dict):
                    detail = _flatten_validation_errors(exc.detail)  # Flatten errors
                    message = (
                        next(iter(detail.values())) if detail else "Validation error"
                    )
                    key = next(iter(detail.keys())) if detail else "Validation error"

                elif isinstance(exc.detail, list):
                    try:
                        detail = _flatten_validation_errors(exc.detail)  # Flatten errors
                        message = (
                            next(iter(detail.values())) if detail else "Validation error"
                        )
                        key = next(iter(detail.keys())) if detail else "Validation error"
                        
                    except Exception as e:
                        detail = {"None": exc.detail[0]}
                        message=exc.detail[0]
                        key=None

                if "unique" in str(detail.values()).lower():
                    response.status_code = status.HTTP_409_CONFLICT

            elif isinstance(exc.detail, dict):
                detail = _flatten_validation_errors(exc.detail)  # Flatten errors
                message = (
                    next(iter(detail.values()))["message"]
                    if detail
                    else "Validation error"
                )
                key = next(iter(detail.keys())) if detail else "Validation error"

            elif isinstance(exc, PermissionDenied):
                message = "You do not have permission to access this resource."
                key = "message"
            
            elif isinstance(exc, NotAuthenticated):
                message="You are not authenticated user."
                key="message"
            
            else:
                detail = response.data
                message = response.status_text

            payload = utils.get_payload(
                request=request,
                detail={},
                message="{0}: {1}".format(key, message),
                extra_information=extra_information,
            )
            
        except Exception as e:
            message=f"None: {exc}"
            payload = utils.get_payload(
                request=request,
                detail={},
                message=message,
                extra_information=extra_information,
            )

        response.data = payload
    return response


class HandleDeleteAttributeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "DELETE":
            try:
                body_unicode = request.body.decode("utf-8")
                request.DELETE = json.loads(body_unicode)
            except json.JSONDecodeError:
                request.DELETE = {}
                # Optionally log the error
                # import logging
                # logger = logging.getLogger(__name__)
                # logger.warning('Invalid JSON in DELETE request body.')

        response = self.get_response(request)
        return response
