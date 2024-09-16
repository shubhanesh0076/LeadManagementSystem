from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from utilities import utils
from rest_framework_simplejwt.authentication import JWTAuthentication
from permissions.custom_permissions import CustomPermission 

class FetchLeadAPIView(APIView):

    authentication_classes = [
        JWTAuthentication
    ]  # check for user is autnenticated or not.
    permission_classes = [CustomPermission]  # check for user has permissions or not

    def get(self, request):
        payload = utils.get_payload(request, message="Lead Information")
        return Response(data=payload, status=status.HTTP_200_OK)