from django.utils import timezone
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from utilities import utils, pagination
from utilities.custom_exceptions import LeadAlreadyAttemptedException
from rest_framework_simplejwt.authentication import JWTAuthentication
from permissions.custom_permissions import CustomPermission
from leads.models import (
    AssignedTO,
    LeadRemark,
    LeadRemarkHistory,
    OptimizedAddressView,
    StudentLeads,
)
from info_bridge.models import DataBridge
from django.db import transaction
from leads.apis.serializers import (
    StudentLeadsSerializer,
    LeadRemarkSerializer,
    LeadRemarkHistorySerializer,
    AssignedTOSerializer,
)

# from accounts.models import User
from utilities.custom_exceptions import UnexpectedError
from django.db.models import Count


class DynamicLeadFilterAPIView(APIView):
    """
    CREATE MATERIALIZED VIEW optimized_address_view as
    SELECT
        db.source,
        db.sub_source,
        c.name AS country_name,
        s.name AS state_name,
        ci.name AS city_name,
        sl.school
    FROM
        info_bridge_databridge db
    JOIN
        leads_studentleads sl ON sl.uploaded_id = db.id
    JOIN
        locations_address a ON a.lead_id = sl.id
    JOIN
        locations_country c ON a.country_id = c.id
    JOIN
        locations_state s ON a.state_id = s.id
    JOIN
        locations_city ci ON a.city_id = ci.id
    WITH DATA;

    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [CustomPermission]

    def get(self, request):
        source = request.GET.get("source", None)
        sub_source = request.GET.get("sub_source", None)
        country = request.GET.get("country", None)
        state = request.GET.get("state", None)
        city = request.GET.get("city", None)
        school = request.GET.get("school", None)

        if source and not any([sub_source, country, state, city, school]):
            sub_source_qs = (
                DataBridge.objects.filter(source=source)
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

        source_qs = DataBridge.objects.values_list("source", flat=True).distinct()
        payload = utils.get_payload(request, detail=source_qs, message="Source List")
        return Response(data=payload, status=status.HTTP_200_OK)


class FetchLeadAPIView(APIView):

    authentication_classes = [
        JWTAuthentication
    ]  # check for user is autnenticated or not.
    permission_classes = [CustomPermission]  # check for user has permissions or not

    def get_query(
        self,
        source: str,
        sub_source: str,
        country: str,
        state: str,
        city: str,
        school: str,
    ):
        query = Q()

        if source:
            query &= Q(uploaded__source=source)
        if sub_source:
            query &= Q(uploaded__sub_source=sub_source)
        if country:
            query &= Q(address__country__name=country)
        if state:
            query &= Q(address__state__name=state)
        if city:
            query &= Q(address__city__name=city)
        if school:
            query &= Q(school=school)
        return query

    def update_is_viewed_field(self, obj: StudentLeads = None) -> None:
        obj.is_attempted = True
        obj.save()

    def get(self, request):
        source = request.GET.get("source", None)
        sub_source = request.GET.get("sub_source", None)
        country = request.GET.get("country", None)
        state = request.GET.get("state", None)
        city = request.GET.get("city", None)
        school = request.GET.get("school", None)

        query = self.get_query(source, sub_source, country, state, city, school)
        student_leads_qs = StudentLeads.objects.select_related(
            "parents_info", "education_info", "general_info", "address"
        ).filter(query, is_attempted=False)

        if student_leads_qs.exists():
            try:
                with transaction.atomic():
                    # get the first student object...
                    first_student_obj = student_leads_qs.first()
                    lead_remark_obj, is_created = LeadRemark.objects.get_or_create(
                        lead_id=first_student_obj.id,
                        defaults={
                            "start_time": timezone.now(),
                            "user_id": request.user.id,
                        },
                    )

                    if is_created:
                        self.update_is_viewed_field(obj=first_student_obj)
                        serialized_student_details = StudentLeadsSerializer(
                            first_student_obj, many=False
                        ).data

                        payload = utils.get_payload(
                            request,
                            detail=serialized_student_details,
                            message="Student details.",
                        )
                        return Response(data=payload, status=status.HTTP_200_OK)

                    else:
                        raise LeadAlreadyAttemptedException(
                            detail=f"This lead is already attempted by: {lead_remark_obj.user.email}. "
                        )

            except LeadAlreadyAttemptedException as laa:
                payload = utils.get_payload(request, message=str(laa))
                return Response(data=payload, status=status.HTTP_409_CONFLICT)

            except Exception as e:
                print("eRROR: ", e)
                payload = utils.get_payload(
                    request, message="An unexpected error occurse."
                )
                return Response(
                    data=payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        payload = utils.get_payload(request, message="There is no leads.")
        return Response(data=payload, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        data = request.data
        lead_id = data.get("lead_id")

        try:
            student_lead = StudentLeads.objects.get(id=lead_id)

        except StudentLeads.DoesNotExist:
            payload = utils.get_payload(
                request, detail={}, message="Student Object not found."
            )
            return Response(data=payload, status=status.HTTP_404_NOT_FOUND)

        st_serializer = StudentLeadsSerializer(
            student_lead, data=request.data, partial=True
        )

        if st_serializer.is_valid():

            with transaction.atomic():
                st_serializer.save()
            payload = utils.get_payload(request, message="Lead successfully updated.")
            return Response(data=payload, status=status.HTTP_200_OK)

        payload = utils.get_payload(request, message=st_serializer.errors)
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)


class LeadRemarkAPIView(APIView):
    authentication_classes = [
        JWTAuthentication
    ]  # check for user is autnenticated or not.
    permission_classes = [CustomPermission]  # check for user has permissions or not
    leadremark_serializer_class = LeadRemarkSerializer

    def get_bool(self, field) -> bool:
        try:
            if field in ["True", "1", "Yes", "yes", "true", True]:
                return True
            return False
        except:
            return False

    def post(self, request):
        data = request.data
        lead_id = data.get("lead_id", None)

        if not lead_id:
            payload = utils.get_payload(
                request, detail={}, message="Lead ID is required."
            )
            return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)

        lead_remark_obj, is_created = LeadRemark.objects.get_or_create(lead_id=lead_id)
        lead_remark_deserialized = self.leadremark_serializer_class(
            lead_remark_obj, data=data, partial=True
        )

        if lead_remark_deserialized.is_valid(raise_exception=True):
            try:
                with transaction.atomic():
                    lead_remark_deserialized.save()
                    payload = utils.get_payload(
                        request,
                        detail={},
                        message="Lead Remark has been successfully updated.",
                    )
                    return Response(data=payload, status=status.HTTP_200_OK)

            except ValueError as ve:
                payload = utils.get_payload(request, detail={}, message=f"{ve}")
                return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)

            except UnexpectedError as e:
                payload = utils.get_payload(
                    request, detail={}, message="An un expected error occurse."
                )
                return Response(
                    data=payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        payload = utils.get_payload(
            request, detail={}, message=lead_remark_deserialized.error_messages
        )
        return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)


class LeadRemarkHistoryAPIView(APIView):
    authentication_classes = [
        JWTAuthentication
    ]  # check for user is autnenticated or not.
    permission_classes = [CustomPermission]  # check for user has permissions or not
    leadremark_history_serializer_class = LeadRemarkHistorySerializer

    def get(self, request):
        records = 10
        lead_id = request.GET.get("lead_id", None)
        lead_remark_history = (
            LeadRemarkHistory.objects.select_related("leadremark")
            .filter(leadremark__lead__id=lead_id)
            .order_by("-updated_at")
            .annotate(count=Count("id"))[:records]
        )

        try:
            lead_remark_history_serialized_data = (
                self.leadremark_history_serializer_class(
                    lead_remark_history, many=True
                ).data
            )
        except Exception as e:
            payload = utils.get_payload(
                request,
                detail=[],
                message="An un-expected error occurse.",
            )
            return Response(data=payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        payload = utils.get_payload(
            request,
            detail=lead_remark_history_serialized_data,
            message="Lead remark history data.",
        )
        return Response(data=payload, status=status.HTTP_200_OK)


class AssignLeadAPIVIew(APIView):
    authentication_classes = [
        JWTAuthentication
    ]  # check for user is autnenticated or not.
    permission_classes = [CustomPermission]  # check for user has permissions or not
    assignto_serializer_class = AssignedTOSerializer

    def post(self, request):

        assignto_deserializer = self.assignto_serializer_class(
            data=request.data, context={"request": request}
        )
        if assignto_deserializer.is_valid(raise_exception=True):
            payload = utils.get_payload(
                request,
                message=f"Lead has been successfully assigned to {request.data.get('assign_to', None)}.",
            )
            return Response(data=payload, status=status.HTTP_200_OK)

        payload = utils.get_payload(
            request, detail={}, message=assignto_deserializer.error_messages
        )
        return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)
