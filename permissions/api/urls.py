from django.urls import path
from permissions.api.views import (
    RoleAPIView,
    PermissionsAPIView,
    AssignPermissionToRoleAPIView,
    AssignRoleToUser,
    UnAssignRoleToUser,
)

app_name = "permissions"

urlpatterns = [
    path("", RoleAPIView.as_view(), name="user-roles"),
    path("permissions/", PermissionsAPIView.as_view(), name="user-permissions"),
    path('assign-permissions-to-role/', AssignPermissionToRoleAPIView.as_view(), name='role-permission-mapping'),
    path('assign-role-to-user/', AssignRoleToUser.as_view(), name='assign-role-to-user'),
    path('un-assign-role-to-user/', UnAssignRoleToUser.as_view(), name='un-assign-role-to-user'),
    
]
