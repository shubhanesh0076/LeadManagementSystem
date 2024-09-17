from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from utilities import utils as ut
from utilities import pagination as pn
from utilities import const
from info_bridge.models import DataBridge
from leads.models import StudentLeads, ParentsInfo
from locations.models import Address
from permissions.custom_permissions import CustomPermission
from rest_framework_simplejwt.authentication import JWTAuthentication
from info_bridge.apis.serializers import DataBridgeSerializer, DataBridgeListSerializer
from info_bridge.apis.upload_service import DataProcessor
from utilities.custom_exceptions import UnexpectedError
from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import NotFound
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404


class DataBridgeAPIView(APIView):

    authentication_classes = [
        JWTAuthentication
    ]  # check for user is autnenticated or not.
    permission_classes = [CustomPermission]  # check for user has permissions or not
    data_bridge_serializer = DataBridgeSerializer
    data_bridge_list_serializer_class = DataBridgeListSerializer

    def get_file_extension(self, filename: str):
        if not filename:
            return ValueError("File can not be None.")
        return filename.split(".")[-1].upper()

    def get(self, request):
        data_bridge_qs = DataBridge.objects.all().order_by("-uploaded_by")

        try:
            paginated_user_qs = pn.paginate_queryset(data_bridge_qs, request)
        except NotFound:
            payload = ut.get_payload(request, detail=[], message="File info list.")
            return Response(data=payload, status=status.HTTP_200_OK)
        serialized_user_qs = self.data_bridge_list_serializer_class(
            paginated_user_qs, many=True
        ).data
        payload = ut.get_payload(
            request,
            detail=serialized_user_qs,
            message="File info list",
            extra_information=pn.get_paginated_response(data=serialized_user_qs),
        )
        return Response(data=payload, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data

        source = data.get("source", None)
        sub_source = data.get("sub_source", None)
        year = data.get("year", None)
        file = data.get("file", None)
        uploaded_by = request.user
        file_name = f"{source}_{sub_source}_{year}_Leads_data.xlsx"

        if not file:
            payload = ut.get_payload(request, message="Source file should be required.")
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        deserialize_data = self.data_bridge_serializer(data=data)
        if deserialize_data.is_valid(raise_exception=True):
            try:
                databridge_qs = DataBridge.objects.filter(file_name=file_name)

                if not databridge_qs.exists():
                    with transaction.atomic():
                        data_bridge_obj = DataBridge.objects.create(
                            source=source,
                            sub_source=sub_source,
                            year=year,
                            uploaded_by=uploaded_by,
                            file_name=file_name,
                        )

                        df_count = DataProcessor.process_upload_file(
                            upload_file=file, uploaded_id=data_bridge_obj.id
                        )
                        data_bridge_obj.lead_count = df_count
                        data_bridge_obj.save()

                else:
                    payload = ut.get_payload(
                        request, detail={}, message="File already exists."
                    )
                    return Response(data=payload, status=status.HTTP_409_CONFLICT)

            except ValueError as ve:
                payload = ut.get_payload(request, detail={}, message=str(ve))
                return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)

            except UnexpectedError as ue:
                payload = ut.get_payload(request, detail={}, message=str(ue))
                return Response(
                    data=payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        payload = ut.get_payload(
            request, message="Leads has been uploaded, successfully."
        )
        return Response(data=payload, status=status.HTTP_200_OK)

    def delete(self, request):
        file_name = request.data.get("file_name", None)
        if not file_name:
            payload = ut.get_payload(request, message="Filename can not be none.")
            return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)

        if self.get_file_extension(file_name) not in const.files_extensions:
            payload = ut.get_payload(request, message="Invalid file extension.")
            return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                try:
                    data_bridge_obj = DataBridge.objects.get(file_name=file_name)
                    student_leads_qs = StudentLeads.objects.filter(
                        uploaded_id=data_bridge_obj.id, is_attempted=False
                    )
                    lead_count = student_leads_qs.count()
                    if lead_count > 0:
                        # Delete related ParentsInfo and Address in bulk
                        ParentsInfo.objects.filter(
                            lead_id__in=student_leads_qs
                        ).delete()
                        Address.objects.filter(lead_id__in=student_leads_qs).delete()

                        # Delete student leads in bulk
                        student_leads_qs.delete()

                        # Update lead count
                        data_bridge_obj.lead_count -= lead_count
                        data_bridge_obj.save()

                        if data_bridge_obj.lead_count == 0:
                            data_bridge_obj.delete()

                    payload = ut.get_payload(
                        request,
                        detail={},
                        message="File and related leads has been deleted successfully.",
                    )
                    return Response(data=payload, status=status.HTTP_204_NO_CONTENT)

                except ObjectDoesNotExist:
                    raise ObjectDoesNotExist("Object doesn't exists.")

        except ObjectDoesNotExist:
            payload = ut.get_payload(request, message="Related file doesn't exists.")
            return Response(data=payload, status=status.HTTP_404_NOT_FOUND)

        except UnexpectedError as ue:
            payload = ut.get_payload(request, message=str(ue))
            return Response(data=payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DataBridgeAppendAPIView(APIView):

    authentication_classes = [
        JWTAuthentication
    ]  # check for user is autnenticated or not.
    permission_classes = [CustomPermission]  # check for user has permissions or not
    data_bridge_serializer = DataBridgeSerializer

    def get_is_extended_var(self, data) -> bool:
        try:
            is_extend_entries = eval(data.get("extend_entries", "False"))
        except:
            is_extend_entries = False
        return is_extend_entries

    def post(self, request):
        data = request.data

        file = data.get("file", None)
        file_name = data.get("file_name", None)
        is_extend_entries = self.get_is_extended_var(data=data)

        if not file:
            payload = ut.get_payload(request, message="Source file should be required.")
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        if not file_name:
            payload = ut.get_payload(request, message="Filename should be required.")
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(is_extend_entries, bool):
            payload = ut.get_payload(
                request, message="extended field should be bool not str or None."
            )
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        if not is_extend_entries:
            payload = ut.get_payload(request, message="Is extend should be True.")
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        try:
            databridge_qs = DataBridge.objects.filter(file_name=file_name)

            if databridge_qs.exists() and is_extend_entries:
                with transaction.atomic():
                    df_count = DataProcessor.process_upload_file(
                        upload_file=file, uploaded_id=databridge_qs[0].id
                    )
                    databridge_qs.update(
                        lead_count=F("lead_count") + df_count
                    )  # Increment lead_count using F expressions (to avoid race conditions)

                payload = ut.get_payload(
                    request,
                    message=f"Leads has been appended successfully into {file_name} file.",
                )
                return Response(data=payload, status=status.HTTP_200_OK)

            else:
                payload = ut.get_payload(
                    request, detail={}, message="File doesn't exists."
                )
                return Response(data=payload, status=status.HTTP_409_CONFLICT)

        except ValueError as ve:
            payload = ut.get_payload(request, detail={}, message=str(ve))
            return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)

        except UnexpectedError as ue:
            payload = ut.get_payload(request, detail={}, message=str(ue))
            return Response(data=payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
