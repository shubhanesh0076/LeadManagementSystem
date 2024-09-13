from django.urls import path
from permissions.api.views import (
    RoleAPIView,
    PermissionsAPIView,
    AssignPermissionToRoleAPIView,
    AssignRoleToUser,
    UnAssignRoleToUser,
    TestingAPIView,
    TestingAPIV2View,
    TestingAPIV3View,
    TestingAPIV4View,
    TestingAPIV5View,
    TestingAPIV6View,
    TestingAPIV7View,
)

app_name = "permissions"

urlpatterns = [
    path("", RoleAPIView.as_view(), name="user-roles"),
    path("permissions/", PermissionsAPIView.as_view(), name="user-permissions"),
    path('assign-permissions-to-role/', AssignPermissionToRoleAPIView.as_view(), name='role-permission-mapping'),
    path('assign-role-to-user/', AssignRoleToUser.as_view(), name='assign-role-to-user'),
    path('un-assign-role-to-user/', UnAssignRoleToUser.as_view(), name='un-assign-role-to-user'),
    
    #  testing APIs...
    path("testing-v1/", TestingAPIView.as_view(), name="user-permissions-v1"),
    path("testing-v2/", TestingAPIV2View.as_view(), name="user-permissions-v2"),
    path("testing-v3/", TestingAPIV3View.as_view(), name="user-permissions-v3"),
    path("testing-v4/", TestingAPIV4View.as_view(), name="user-permissions-v4"),
    path("testing-v5/", TestingAPIV5View.as_view(), name="user-permissions-v5"),
    path("testing-v6/", TestingAPIV6View.as_view(), name="user-permissions-v6"),
    path("testing-v7/", TestingAPIV7View.as_view(), name="user-permissions-v7"),
]
