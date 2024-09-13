from rest_framework.views import APIView
from permissions.api.serializers import (
    CreateRoleSerializer,
    UpdateRoleSerializer,
    RoleListSerializer,
    CustomPermissionSerializer,
    CreatePermissionSerializer,
)
from permissions.models import (
    Role,
    CustomPermissions,
    RoleCustomPermissionMapping,
    UserRoleMapping,
)
from accounts.models import User
from utilities import utils
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError, transaction
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.authentication import JWTAuthentication
from permissions.custom_permissions import CustomPermission


class RoleAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [CustomPermission]

    serializer_role_list_class = RoleListSerializer
    serializer_role_class = CreateRoleSerializer
    serializer_update_role_class = UpdateRoleSerializer
    role_ = Role.objects

    def get(self, request):
        role_qs = self.role_.all().order_by("created_at")
        serialized_role_data = self.serializer_role_list_class(role_qs, many=True).data

        payload = utils.get_payload(
            request, detail=serialized_role_data, message="Role List."
        )
        return Response(data=payload, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        serialized_data = self.serializer_role_class(data=data)

        try:
            serialized_data.is_valid(raise_exception=True)
            serialized_data.save()

        except IntegrityError:
            payload = utils.get_payload(
                request, detail={}, message="related role already exists."
            )
            return Response(data=payload, status=status.HTTP_409_CONFLICT)

        payload = utils.get_payload(request, detail=data, message="Role created.")
        return Response(data=payload, status=status.HTTP_200_OK)

    def patch(self, request):
        data = request.data
        slug = data.get("slug", None)

        if not slug:
            payload = utils.get_payload(
                request, detail={}, message=f"old role name field can not be None."
            )
            return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)

        try:
            role_obj = Role.objects.get(slug=slug)

        except ObjectDoesNotExist:
            payload = utils.get_payload(
                request, detail={}, message=f"Object doesn't exists."
            )
            return Response(data=payload, status=status.HTTP_404_NOT_FOUND)

        deserialized_data = self.serializer_update_role_class(
            instance=role_obj, data=data, partial=True
        )
        try:
            if deserialized_data.is_valid():
                deserialized_data.save()

                payload = utils.get_payload(
                    request, detail={}, message="Role updated successfully."
                )
                return Response(data=payload, status=status.HTTP_200_OK)

        except IntegrityError:
            payload = utils.get_payload(
                request, detail={}, message="related role already exists."
            )
            return Response(data=payload, status=status.HTTP_409_CONFLICT)

    def delete(self, request):

        slug = request.DELETE.get("slug", [])
        if not slug:
            payload = utils.get_payload(request, message="Role name is required.")
            return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(slug, str):
            payload = utils.get_payload(
                request, message="slug should be list formated not str."
            )
            return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)

        try:
            role_qs = self.role_.filter(slug__in=slug)
            if not role_qs:
                payload = utils.get_payload(request, message="Role obj doesn't exists.")
                return Response(data=payload, status=status.HTTP_404_NOT_FOUND)

            role_qs.delete()
            payload = utils.get_payload(request, message="Role obj deleted.")
            return Response(data=payload, status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            payload = utils.get_payload(
                request, detail={}, message="An Un-expected error occurse."
            )
            return Response(data=payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PermissionsAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [CustomPermission]

    serializer_permission_list_class = CustomPermissionSerializer
    serializer_create_permission_class = CreatePermissionSerializer
    custom_permissions = CustomPermissions.objects

    def get(self, request):
        custom_permissions_qs = self.custom_permissions.all().order_by("created_at")
        custom_permission_data = self.serializer_permission_list_class(
            custom_permissions_qs, many=True
        ).data

        payload = utils.get_payload(
            request, detail=custom_permission_data, message="Permissions List."
        )
        return Response(data=payload, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data

        if not data:
            payload = utils.get_payload(
                request, detail={}, message=f"Empty list can not be pass."
            )
            return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(data, list):
            payload = utils.get_payload(
                request,
                detail={},
                message=f"In body data should be in list of Object format.",
            )
            return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)

        serialized_data = self.serializer_create_permission_class(data=data, many=True)
        try:
            serialized_data.is_valid()
            permissions = [CustomPermissions(**item_data) for item_data in data]
            CustomPermissions.objects.bulk_create(permissions)

        except IntegrityError as e:
            payload = utils.get_payload(
                request, detail={}, message=f"related permission already exists: {e}"
            )
            return Response(data=payload, status=status.HTTP_409_CONFLICT)

        payload = utils.get_payload(request, detail=data, message="Role created.")
        return Response(data=payload, status=status.HTTP_200_OK)

    # def patch(self, request):
    # data = request.data
    # slug = data.get("slug", None)

    # if not slug:
    #     payload = utils.get_payload(
    #         request, detail={}, message=f"old role name field can not be None."
    #     )
    #     return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)

    # try:
    #     role_obj = Role.objects.get(slug=slug)

    # except ObjectDoesNotExist:
    #     payload = utils.get_payload(
    #         request, detail={}, message=f"Object doesn't exists."
    #     )
    #     return Response(data=payload, status=status.HTTP_404_NOT_FOUND)

    # deserialized_data = self.serializer_update_role_class(
    #     instance=role_obj, data=data, partial=True
    # )
    # try:
    #     if deserialized_data.is_valid():
    #         deserialized_data.save()

    #         payload = utils.get_payload(
    #             request, detail={}, message="Role updated successfully."
    #         )
    #         return Response(data=payload, status=status.HTTP_200_OK)

    # except IntegrityError:
    #     payload = utils.get_payload(
    #         request, detail={}, message="related role already exists."
    #     )
    #     return Response(data=payload, status=status.HTTP_409_CONFLICT)

    # def delete(self, request):

    #     slug = request.DELETE.get("slug", [])
    #     if not slug:
    #         payload = utils.get_payload(request, message="Role name is required.")
    #         return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)

    #     if isinstance(slug, str):
    #         payload = utils.get_payload(
    #             request, message="slug should be list formated not str."
    #         )
    #         return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)

    #     try:
    #         role_qs = self.role_.filter(slug__in=slug)
    #         if not role_qs:
    #             payload = utils.get_payload(request, message="Role obj doesn't exists.")
    #             return Response(data=payload, status=status.HTTP_404_NOT_FOUND)

    #         role_qs.delete()
    #         payload = utils.get_payload(request, message="Role obj deleted.")
    #         return Response(data=payload, status=status.HTTP_204_NO_CONTENT)

    #     except Exception as e:
    #         payload = utils.get_payload(
    #             request, detail={}, message="An Un-expected error occurse."
    #         )
    #         return Response(data=payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AssignPermissionToRoleAPIView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [CustomPermission]

    def post(self, request):
        data = request.data

        if not data:
            payload = utils.get_payload(
                request, detail={}, message="Empty list can not be pass."
            )
            return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(data, list):
            payload = utils.get_payload(
                request,
                detail={},
                message=f"In body, data should be in list of Object format.",
            )
            return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)
        try:
            with transaction.atomic():
                for _ in data:
                    try:
                        role_obj = Role.objects.get(role_name=_["role_name"])
                        custom_permission_obj = CustomPermissions.objects.get(
                            method=_["method"], endpoint=_["endpoint"]
                        )
                        RoleCustomPermissionMapping.objects.update_or_create(
                            role_id=role_obj.id,
                            custom_permission_id=custom_permission_obj.id,
                            defaults={},
                        )
                    except ObjectDoesNotExist:
                        raise ObjectDoesNotExist("Object doesn't exists.")

        except ObjectDoesNotExist as e:
            payload = utils.get_payload(
                request,
                detail={},
                message="Object doesn't exists",
            )
            return Response(data=payload, status=status.HTTP_404_NOT_FOUND)

        payload = utils.get_payload(
            request, detail=[], message="Role successfully assoigned to permissions."
        )
        return Response(data=payload, status=status.HTTP_200_OK)


class AssignRoleToUser(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [CustomPermission]
    
    def post(self, request):
        data = request.data

        email = data.get("email", None)
        role_name = data.get("role_name", [])

        if not email:
            payload = utils.get_payload(
                request,
                detail={},
                message=f"User email should be required.",
            )
            return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(role_name, list):
            payload = utils.get_payload(
                request,
                detail={},
                message=f"Roles should be required in list format",
            )
            return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)

        if not role_name:
            payload = utils.get_payload(
                request,
                detail={},
                message=f"Role can not be None.",
            )
            return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)

        if email and role_name:
            try:
                user_obj = User.objects.get(email=email)
            except ObjectDoesNotExist:
                payload = utils.get_payload(
                    request, message=f"{email} user doesn't exists."
                )
                return Response(data=payload, status=status.HTTP_404_NOT_FOUND)

            role_obj = Role.objects.filter(role_name__in=role_name)
            if not role_obj:
                payload = utils.get_payload(
                    request, message=f"Related roles doesn't exists."
                )
                return Response(data=payload, status=status.HTTP_404_NOT_FOUND)

            try:
                for role in role_obj:
                    UserRoleMapping.objects.update_or_create(
                        user_id=user_obj.id, role_id=role.id
                    )
            except Exception as e:
                print("An un-expected error Occurse: ", e)
                payload = utils.get_payload(
                    request, message="An un expected error occurse."
                )
                return Response(
                    data=payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        payload = utils.get_payload(
            request,
            detail={},
            message=f"Role successfully assigned to user({email}).",
        )
        return Response(data=payload, status=status.HTTP_200_OK)


class UnAssignRoleToUser(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [CustomPermission]

    def delete(self, request):
        data = request.data

        email = data.get("email", None)
        role_name = data.get("role_name", [])

        if not email:
            payload = utils.get_payload(
                request,
                detail={},
                message=f"User email should be required.",
            )
            return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(role_name, list):
            payload = utils.get_payload(
                request,
                detail={},
                message=f"Roles should be required in list format",
            )
            return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)

        if not role_name:
            payload = utils.get_payload(
                request,
                detail={},
                message=f"Role can not be None.",
            )
            return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)

        if email and role_name:
            try:
                user_obj = User.objects.get(email=email)
            except ObjectDoesNotExist:
                payload = utils.get_payload(
                    request, message=f"{email} user doesn't exists."
                )
                return Response(data=payload, status=status.HTTP_404_NOT_FOUND)

            role_obj = Role.objects.filter(role_name__in=role_name)
            if not role_obj:
                payload = utils.get_payload(
                    request, message=f"Related roles doesn't exists."
                )
                return Response(data=payload, status=status.HTTP_404_NOT_FOUND)

            try:
                un_assign_role_from_user_qs = UserRoleMapping.objects.filter(
                    user=user_obj, role__in=role_obj
                )
                if un_assign_role_from_user_qs.exists():
                    un_assign_role_from_user_qs.delete()

            except Exception as e:
                print("An un-expected error Occurse: ", e)
                payload = utils.get_payload(
                    request, message="An un expected error occurse."
                )
                return Response(
                    data=payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        payload = utils.get_payload(
            request,
            detail={},
            message=f"Role un-assiged successfully, from {email}",
        )
        return Response(data=payload, status=status.HTTP_200_OK)


class TestingAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [CustomPermission]

    def get(self, request):
        payload = utils.get_payload(request, detail={}, message="Permissions List.")
        return Response(data=payload, status=status.HTTP_200_OK)


class TestingAPIV2View(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [CustomPermission]

    def post(self, request):
        payload = utils.get_payload(request, detail={}, message="Permissions List.")
        return Response(data=payload, status=status.HTTP_200_OK)


class TestingAPIV3View(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [CustomPermission]

    def get(self, request):
        payload = utils.get_payload(request, detail={}, message="Permissions List.")
        return Response(data=payload, status=status.HTTP_200_OK)


class TestingAPIV4View(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [CustomPermission]

    def delete(self, request):
        payload = utils.get_payload(request, detail={}, message="Permissions List.")
        return Response(data=payload, status=status.HTTP_200_OK)


class TestingAPIV5View(APIView):

    def patch(self, request):
        payload = utils.get_payload(request, detail={}, message="Permissions List.")
        return Response(data=payload, status=status.HTTP_200_OK)


class TestingAPIV6View(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [CustomPermission]
    
    def get(self, request):
        payload = utils.get_payload(request, detail={}, message="Permissions List.")
        return Response(data=payload, status=status.HTTP_200_OK)


class TestingAPIV7View(APIView):

    def post(self, request):
        payload = utils.get_payload(request, detail={}, message="Permissions List.")
        return Response(data=payload, status=status.HTTP_200_OK)
