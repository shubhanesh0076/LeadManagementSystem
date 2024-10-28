from django.utils import timezone
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from utilities import utils, pagination
from utilities.custom_exceptions import LeadAlreadyAttemptedException
from rest_framework_simplejwt.authentication import JWTAuthentication
from permissions.custom_permissions import CustomPermission
from leads.models import (AssignedTO, FollowUp, LeadRemark, LeadRemarkHistory,
    OptimizedAddressView, ParentsInfo, StudentLeads)
from info_bridge.models import DataBridge
from leads.apis.serializers import (
    StudentLeadsSerializer,
    LeadRemarkSerializer,
    LeadRemarkHistorySerializer,
    AssignedTOSerializer,
    FollowUpSerializer,
    PendingLeadsSerializer,
    ReferredLeadsSerializer,
    LeadDistributionSerializer,
)
from utilities.custom_exceptions import UnexpectedError, PageNotFound
from django.db.models import Count
from django.db import connection, transaction
from leads.apis.lead_permission import IsLeadOwnerOrAdmin, LeadTypePermissions
from LMS.settings import AUTH_PASSWORD_VALIDATORS
from utilities.utils import StandardResultsSetPagination
from permissions.models import LeadsDistributions


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
        source = request.GET.get("source")
        sub_source = request.GET.get("sub_source")
        country = "INDIA"  # Assuming fixed country
        state = request.GET.get("state")
        city = request.GET.get("city")
        school = request.GET.get("school")

        # Superuser bypasses permissions
        if not request.user.is_superuser:
            lead_distribution_qs = LeadsDistributions.objects.filter(user_id=request.user.id)
            if not lead_distribution_qs.exists():
                payload = utils.get_payload(request, message="There are no leads in your quotas.")
                return Response(data=payload, status=status.HTTP_200_OK)

            # Extract user permission data
            user_permission = lead_distribution_qs.first()
            ld_source = user_permission.source or []
            ld_sub_source = user_permission.sub_source or []
            ld_state = user_permission.state or []
            ld_city = user_permission.city or []
            ld_school = user_permission.school or []
            

        # Helper function to build queryset filters dynamically
        def filter_queryset():
            filters = Q(country_name=country)
            if source:
                filters &= Q(source__in=ld_source if source in ld_source else [source])
            if sub_source:
                filters &= Q(sub_source__in=ld_sub_source  if sub_source in ld_sub_source else [sub_source])
            if state:
                filters &= Q(state_name__in=ld_state if state in ld_state else [state])
            if city:
                filters &= Q(city_name__in=ld_city if city in ld_city else [city])
            if school:
                filters &= Q(school__in=ld_school if school in ld_school else [school])
            return filters

        # Determine the appropriate queryset and response message
        if source and not any([sub_source, state, city, school]):
            if request.user.is_superuser or ld_sub_source is None or not ld_sub_source:
                sub_source_qs = DataBridge.objects.filter(source=source).values_list("sub_source", flat=True).distinct()
            else:
                sub_source_qs = DataBridge.objects.filter(source__in=ld_source, sub_source__in=ld_sub_source).values_list("sub_source", flat=True).distinct()
            message = "Sub Source List"
            detail = sub_source_qs
            
        elif source and sub_source and not any([state, city, school]):
            if request.user.is_superuser or ld_state is None or not ld_state:
                state_qs = OptimizedAddressView.objects.filter(filter_queryset()).values_list("state_name", flat=True).distinct()
            else:
                state_qs = OptimizedAddressView.objects.filter(filter_queryset(), state_name__in=ld_state).values_list("state_name", flat=True).distinct()
            message = "State List"
            detail = state_qs
            
        elif source and sub_source and state and not city and not school:
            if request.user.is_superuser or ld_city or not ld_city:
                city_qs = OptimizedAddressView.objects.filter(filter_queryset()).values_list("city_name", flat=True).distinct()
            else:
                city_qs = OptimizedAddressView.objects.filter(filter_queryset(), city_name__in=ld_city).values_list("city_name", flat=True).distinct()
            message = "City List"
            detail = city_qs
            
        elif source and sub_source and state and city and not school:
            if request.user.is_superuser or ld_school or not ld_school:
                school_qs = OptimizedAddressView.objects.filter(filter_queryset()).values_list("school", flat=True).distinct()
            else:
                school_qs = OptimizedAddressView.objects.filter(filter_queryset(), school__in=ld_school).values_list("school", flat=True).distinct()
            message = "School List"
            detail = school_qs
            
        else:
            source_qs = DataBridge.objects.filter(source__in=ld_source, ).values_list("source", flat=True).distinct()
            message = "Source List"
            detail = source_qs

        payload = utils.get_payload(request, detail=detail, message=message)
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

    def update_is_viewed_field(self, obj) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE leads_studentleads SET is_attempted = TRUE WHERE id = %s",
                [obj.id],
            )

    def get(self, request):
        source = request.GET.get("source", None)
        sub_source = request.GET.get("sub_source", None)
        country = request.GET.get("country", None)
        state = request.GET.get("state", None)
        city = request.GET.get("city", None)
        school = request.GET.get("school", None)
        lead_id = request.GET.get("lead_id", None)

        if lead_id:
            is_leadowner = IsLeadOwnerOrAdmin()
            student_lead = (
                StudentLeads.objects.filter(id=lead_id)
                .prefetch_related("lead_remark", "student_lead")
                .first()
            )

            if not is_leadowner.has_object_permission(request, None, student_lead):
                payload = utils.get_payload(
                    request, message="You do not have access to this lead."
                )
                return Response(data=payload, status=status.HTTP_403_FORBIDDEN)

            serialized_student_details = StudentLeadsSerializer(
                student_lead, many=False
            ).data

            payload = utils.get_payload(
                request,
                detail=serialized_student_details,
                message="Student details.",
            )
            return Response(data=payload, status=status.HTTP_200_OK)

        else:
            if not request.user.is_superuser:
                lead_distribution_qs = LeadsDistributions.objects.filter(user_id=request.user.id)
                
                # Extract user permission data
                user_permission = lead_distribution_qs.first()
                ld_source = user_permission.source or []
                ld_sub_source = user_permission.sub_source or []
                ld_state = user_permission.state or []
                ld_city = user_permission.city or []
                ld_school = user_permission.school or []
                
                # check for lead permission...
                message=None
                if (source and ld_source):
                    if source not in ld_source:
                        message=f"You have no permission to access the {source} leads."
                if sub_source and ld_sub_source:
                    if sub_source not in ld_sub_source:
                        message = f"You have no permission to access the {sub_source} leads."
                if state and ld_state:
                    if state not in ld_state:
                        message = f"You have no permission to access the {state} leads."
                if city and ld_city:
                    if city not in ld_city:
                        message = f"You have no permission to access the {city} leads."
                if message:
                    payload = utils.get_payload(request, message=message)
                    return Response(data=payload, status=status.HTTP_403_FORBIDDEN)
            
            query = self.get_query(source, sub_source, country, state, city, school)
            student_leads_qs = StudentLeads.objects.select_related(
                "parents_info", "education_info", "general_info", "address"
            ).filter(query, is_attempted=False)

            if student_leads_qs.exists():
                try:
                    
                    # db transaction start over here...
                    with transaction.atomic():
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
                    payload = utils.get_payload(
                        request, message="An unexpected error occurse."
                    )
                    return Response(data=payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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


class StatusWiseLeadAPIView(APIView):

    authentication_classes = [
        JWTAuthentication
    ]  # check for user is autnenticated or not.
    permission_classes = [CustomPermission]  # check for user has permissions or not

    def handle_pending(self, lead_status, user_id):
        pending_leads_qs = LeadRemark.objects.filter(
            lead_status=lead_status, user_id=user_id
        ).order_by("-updated_at")
        message = "Pending"
        return pending_leads_qs, message

    def handle_referred(self, lead_status, user_id):
        # Add operation for "REFERRED"
        assigned_to_lead_qs = AssignedTO.objects.filter(assign_by__id=user_id).order_by(
            "-assigned_at"
        )
        message = "Assigned"
        return assigned_to_lead_qs, message

    def handle_rejected(self, lead_status, user_id):
        # Add operation for "REJECTED"
        un_qualified_ = "UNQUALIFIED"
        lost_ = "LOST"
        query = Q(lead_status=un_qualified_) | Q(lead_status=lost_)
        rejected_lead_remark_qs = LeadRemark.objects.filter(
            query, user_id=user_id
        ).order_by("-updated_at")
        message = "Rejected"

        return rejected_lead_remark_qs, message

    def handle_completed(self, lead_status, user_id):
        # Add operation for "COMPLETED"
        completed_lead_qs = LeadRemark.objects.filter(
            lead_status=lead_status, user_id=user_id
        ).order_by("-updated_at")
        message = "Completed"
        return completed_lead_qs, message

    def handle_followup(self, lead_status, user_id):
        followup_leads = FollowUp.objects.filter(
            lead__lead_remark__lead_status=lead_status, follow_up_by_id=user_id
        ).order_by("-follow_up_date")
        message = "Followup"
        return followup_leads, message

    def get(self, request):
        user_id = request.GET.get("user_id", None)
        lead_status = request.GET.get("lead_status", None)
        lead_permissions = LeadTypePermissions()

        lead_status_operations = {
            "PENDING": self.handle_pending(lead_status, user_id),
            "REFERRED": self.handle_referred(lead_status, user_id),
            "REJECTED": self.handle_rejected(lead_status, user_id),
            "COMPLETED": self.handle_completed(lead_status, user_id),
            "FOLLOWUP": self.handle_followup(lead_status, user_id),
        }

        lead_serializers_dic = {
            "PENDING": PendingLeadsSerializer,
            "REFERRED": ReferredLeadsSerializer,
            "REJECTED": PendingLeadsSerializer,
            "COMPLETED": PendingLeadsSerializer,
            "FOLLOWUP": FollowUpSerializer,
        }

        if lead_status in lead_status_operations:
            try:
                lead_qs, _message = lead_status_operations[lead_status]
                lead_status_operations[lead_status]

                if lead_permissions.has_object_permission(request, None, lead_qs):
                    paginated_user_qs = pagination.paginate_queryset(lead_qs, request)
                    serialized_lead_data = lead_serializers_dic[lead_status](
                        paginated_user_qs, many=True
                    ).data

                    payload = utils.get_payload(
                        request,
                        detail=serialized_lead_data,
                        message=f"{_message} Leads",
                        extra_information=pagination.get_paginated_response(
                            data=serialized_lead_data
                        ),
                    )
                    return Response(data=payload, status=status.HTTP_200_OK)

                payload = utils.get_payload(
                    request,
                    message=f"You do not have permission to access another user's {_message} leads.",
                )
                return Response(data=payload, status=status.HTTP_403_FORBIDDEN)

            except PageNotFound as pnf:
                payload = utils.get_payload(request, detail=[], message=f"{pnf}")
                return Response(data=payload, status=status.HTTP_404_NOT_FOUND)

            except Exception as e:
                print("ERror: ", e)
                payload = utils.get_payload(
                    request, message="An un expected error Occurse.", detail=[]
                )
                return Response(
                    data=payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            payload = utils.get_payload(
                request,
                message="Bad Request, due to Invalid lead status pass.",
                detail=[],
            )
            return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)


class LeadDistributionAPIView(APIView):

    authentication_classes = [
        JWTAuthentication
    ]  # check for user is autnenticated or not.
    permission_classes = [CustomPermission]  # check for user has permissions or not
    lead_distribution_serializer = LeadDistributionSerializer

    def post(self, request):
        data = request.data
        deserialized_lead_distribution = self.lead_distribution_serializer(
            data=data, context={"user_id": data.get("user_id", None)}
        )
        if deserialized_lead_distribution.is_valid(raise_exception=True):
            try:
                deserialized_lead_distribution.save()
                payload = utils.get_payload(
                    request, message="Successfully distrubute the leads to user."
                )
                return Response(data=payload, status=status.HTTP_201_CREATED)

            except ValueError as ve:
                payload = utils.get_payload(request, message=f"{ve}")
                return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)

            except UnexpectedError as e:
                payload = utils.get_payload(
                    request, message="An un-expected error occurse."
                )
                return Response(
                    data=payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        payload = utils.get_payload(
            request, message=deserialized_lead_distribution.error_messages
        )
        return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)


from rest_framework import generics
from django.utils import timezone
from datetime import timedelta
from notifications.models import Notification
from notifications.apis.serializers import NotificationSerializer
from manage import main
# from rest_framework.permissions import IsAuthenticated

class WeeklyNotificationsView(APIView):
    
    authentication_classes = [
        JWTAuthentication
    ]  # check for user is autnenticated or not.
    permission_classes = [CustomPermission]  # check for user has permissions or not
    serializer_class = NotificationSerializer

    def get(self, request):
        now = timezone.now()
        one_week_ago = now - timedelta(weeks=1)
        qs = NotificationSerializer(Notification.objects.filter(user=self.request.user, created_at__gte=one_week_ago).order_by('-created_at'), many=True).data
        payload = utils.get_payload(request, detail=qs, message="Notification List")
        return Response(data=payload, status=status.HTTP_200_OK)
