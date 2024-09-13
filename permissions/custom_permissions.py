# permissions.py
from rest_framework.permissions import BasePermission
from utilities import utils
from permissions.models import RoleCustomPermissionMapping
# from rest_framework.response import Response
# from rest_framework import status
from rest_framework.exceptions import PermissionDenied, NotAuthenticated


class CustomPermission(BasePermission):
    """
    Custom permission to check if the user has the required permissions.

    This permission checks if the authenticated user has a specific role or
    permission to access a particular view.
    """

    def get_auth_token(self, request):
        auth_token = request.headers.get("Authorization", None).split(" ")[1]
        return auth_token

    def get_roles(self, decoded_token: dict):
        return decoded_token["roles"]

    def get_current_endpoint(self, request):
        return request.get_full_path()

    def is_permitted(self, roles: list, current_endppoint: str) -> bool:
        return RoleCustomPermissionMapping.objects.filter(
            role__role_name__in=roles, custom_permission__endpoint=current_endppoint
        ).exists()

    def has_permission(self, request, view):
        """
        Check if the user has the required permission.

        Args:
            request (Request): The HTTP request being processed.
            view (View): The view being accessed.

        Returns:
            bool: True if the user has the permission, False otherwise.
        """

        # Example: Check if the user is authenticated and has a specific role
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated(detail="You are not authenticated user.")

        auth_token = self.get_auth_token(request)
        decoded_token = utils.decode_jwt_token(auth_token)
        roles = self.get_roles(decoded_token)

        if "admin" not in roles or not request.user.is_superuser:
            current_endppoint = self.get_current_endpoint(request)
            has_permission = self.is_permitted(
                roles=roles, current_endppoint=current_endppoint
            )

            if not has_permission:
                raise PermissionDenied(detail='You do not have permission to access this resource.')
        return True
