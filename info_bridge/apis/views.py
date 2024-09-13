from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from utilities import utils as ut
from info_bridge.models import DataBridge
from permissions.custom_permissions import CustomPermission
from rest_framework_simplejwt.authentication import JWTAuthentication
from info_bridge.apis.serializers import DataBridgeSerializer
from info_bridge.apis.upload_service import DataProcessor
from utilities.custom_exceptions import UnexpectedError
from django.db import transaction
from django.db.models import F


class DataBridgeAPIView(APIView):

    authentication_classes = [
        JWTAuthentication
    ]  # check for user is autnenticated or not.
    permission_classes = [CustomPermission]  # check for user has permissions or not
    data_bridge_serializer = DataBridgeSerializer

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
                        df_count = DataProcessor.process_upload_file(upload_file=file)
                        DataBridge.objects.create(
                            source=source,
                            sub_source=sub_source,
                            year=year,
                            uploaded_by=uploaded_by,
                            file_name=file_name,
                            lead_count=df_count,
                        )

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
            payload = ut.get_payload(request, message="extended field should be bool not str or None.")
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)
        
        if not is_extend_entries:
            payload = ut.get_payload(request, message="Is extend should be True.")
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        try:
            databridge_qs = DataBridge.objects.filter(file_name=file_name)

            if databridge_qs.exists() and is_extend_entries:
                with transaction.atomic():
                    df_count = DataProcessor.process_upload_file(upload_file=file)
                    print("DF COUNT: ", df_count)
                    databridge_qs.update(
                        lead_count=F("lead_count") + df_count
                    )  # Increment lead_count using F expressions (to avoid race conditions)
                
                payload = ut.get_payload(
                    request, message=f"Leads has been appended successfully into {file_name} file."
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
