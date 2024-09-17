from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from utilities import utils
from rest_framework_simplejwt.authentication import JWTAuthentication
from permissions.custom_permissions import CustomPermission
from leads.models import OptimizedAddressView


class DynamicLeadFilterAPIView(APIView):
    def get(self, request):
        source = request.GET.get("source", None)
        sub_source = request.GET.get("sub_source", None)
        country = request.GET.get("country", None)
        state = request.GET.get("state", None)
        city = request.GET.get("city", None)
        school = request.GET.get("school", None)

        if source and not any([sub_source, country, state, city, school]):
            sub_source_qs = (
                OptimizedAddressView.objects.filter(source=source)
                .values_list("sub_source", flat=True)
                .distinct()
            )
            message = "Sub Source List"
            payload = utils.get_payload(request, detail=sub_source_qs, message=message)
            return Response(data=payload, status=status.HTTP_200_OK)

        elif source and sub_source and not any([country, state, city, school]):
            country_qs = (
                OptimizedAddressView.objects.filter(
                    source=source, sub_source=sub_source
                )
                .values_list("country_name", flat=True)
                .distinct()
            )
            message = "Country List"
            payload = utils.get_payload(
                request, detail=country_qs, message="Country List."
            )
            return Response(data=payload, status=status.HTTP_200_OK)

        elif source and sub_source and country and not any([state, city, school]):
            state_qs = (
                OptimizedAddressView.objects.filter(
                    source=source, sub_source=sub_source, country_name=country
                )
                .values_list("state_name", flat=True)
                .distinct()
            )
            message = "State List"
            payload = utils.get_payload(request, detail=state_qs, message="State List.")
            return Response(data=payload, status=status.HTTP_200_OK)

        elif source and sub_source and country and state and not city and not school:
            city_qs = (
                OptimizedAddressView.objects.filter(
                    source=source,
                    sub_source=sub_source,
                    country_name=country,
                    state_name=state,
                )
                .values_list("city_name", flat=True)
                .distinct()
            )
            message = "City List"
            payload = utils.get_payload(request, detail=city_qs, message=message)
            return Response(data=payload, status=status.HTTP_200_OK)

        elif source and sub_source and country and state and city and not school:
            school_qs = (
                OptimizedAddressView.objects.filter(
                    source=source,
                    sub_source=sub_source,
                    country_name=country,
                    state_name=state,
                    city_name=city,
                )
                .values_list("school", flat=True)
                .distinct()
            )
            message = "School List"
            payload = utils.get_payload(request, detail=school_qs, message=message)
            return Response(data=payload, status=status.HTTP_200_OK)

        source_qs = OptimizedAddressView.objects.values_list(
            "source", flat=True
        ).distinct()
        payload = utils.get_payload(request, detail=source_qs, message="Source List")
        return Response(data=payload, status=status.HTTP_200_OK)


class FetchLeadAPIView(APIView):

    authentication_classes = [
        JWTAuthentication
    ]  # check for user is autnenticated or not.
    permission_classes = [CustomPermission]  # check for user has permissions or not

    def get(self, request):

        source = "excel"
        sub_source = "12th"
        country = "India"
        state = "UP"
        city = "Noida"
        school = "Galgotia University."

        payload = utils.get_payload(request, message="Lead Information")
        return Response(data=payload, status=status.HTTP_200_OK)
