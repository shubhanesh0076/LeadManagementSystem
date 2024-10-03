import re
import random
import string
import jwt
from typing import Any
from utilities import constants as const
from django.utils.text import slugify
from django.conf import settings
from datetime import datetime
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.exceptions import NotFound


class Utils:

    @staticmethod
    def email_validate(email: str = None) -> bool:
        if re.match(const.email_validator_pattern, email):
            return True
        return False

    @staticmethod
    def get_payload(
        request,
        detail={},
        message: str = None,
        extra_information: dict = {},
    ) -> dict:
        return {
            "is_authenticated": Utils().is_authenticated_status(request),
            "message": message,
            "detail": detail,
            "extra_information": extra_information,
        }

    def is_authenticated_status(self, request) -> bool:
        """
        check the authentication status...
        """
        try:
            if request.user.is_authenticated:
                return True
            return False

        except Exception as e:
            return False

    def custome_message(self, error):
        if "to_user" in error.detail:
            return str(error.detail.get("to_user")[0])
        elif "non_field_errors" in error.detail:
            return str(error.detail.get("non_field_errors")[0])
        else:
            return "Invalid request."

    def random_string_generator(
        self, size=10, chars=string.ascii_lowercase + string.digits
    ):
        return "".join(random.choice(chars) for _ in range(size))

    def unique_slug_generator(self, instance, field_name, new_slug=None):
        if new_slug is not None:
            slug = new_slug
        else:
            slug = slugify(field_name)
        Klass = instance.__class__
        qs_exists = Klass.objects.filter(slug=slug).exists()

        if qs_exists:
            new_slug = "{slug}-{randstr}".format(
                slug=slug, randstr=self.random_string_generator(size=4)
            )

            return self.unique_slug_generator(instance, field_name, new_slug=new_slug)
        return slug

    def decode_jwt_token(self, token):
        try:
            # Decode the token without verification (this only decodes the payload)
            decoded_payload = jwt.decode(
                jwt=token, key=settings.SECRET_KEY, algorithms=settings.HS256_KEY
            )
            return decoded_payload
        except jwt.DecodeError as e:
            print("Failed to decode token:", str(e))
            return None

    def convert_into_desired_dtime_format(
        self, obj, datetime_format="%d %b, %Y %H:%M:%S"
    ):
        return datetime.strftime(obj, datetime_format)

    def datetime_difference(self, start_timestamp, end_timestamp):
        "returns the time difference between two timestamps in Min."
        # if start_time or end_time is None:
        #     raise "timestamp can not be None."
        return (end_timestamp - start_timestamp).total_seconds() // 60


class CustomPageNumberPagination(PageNumberPagination):
    page_size = const.page_size
    page_size_query_param = const.page_size_query_param
    max_page_size = const.max_page_size

    def get_paginated_response(self, data):
        payload = {
            "pagination_info": {
                "links": {
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                },
                "count": self.page.paginator.count,
            }
        }
        return payload

    def paginate_queryset(self, queryset, request, view=None):
        try:
            # Attempt to paginate the queryset using the parent class method
            return super().paginate_queryset(queryset, request, view)
        except NotFound:
            # Handle the case where the requested page is invalid
            raise NotFound(detail="Invalid page. Please select a valid page number.")

    def get_custom_error_response(self):
        return Response(
            {"detail": "Invalid page. Please select a valid page number."}, status=404
        )


class StandardResultsSetPagination(CustomPageNumberPagination): ...
