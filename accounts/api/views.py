from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from permissions.custom_permissions import CustomPermission

from accounts.api.serializers import (
    CreateUserSerializer,
    UserSerializer,
    CustomTokenObtainPairSerializer,
    CustomTokenRefreshSerializer,
    UserListSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from utilities import utils, pagination
from rest_framework.exceptions import ValidationError
from django.db import IntegrityError
from accounts.models import User
from django.db.models import Prefetch
from permissions.models import Role, UserRoleMapping
from rest_framework.exceptions import NotFound


# from django.core.exceptions import ObjectDoesNotExist
# from django.contrib.auth import authenticate, login, logout


class LoginAPIView(TokenObtainPairView):
    """
    API view for user login.

    This view handles the user login process by extending the TokenObtainPairView
    from Django REST Framework's SimpleJWT package. It authenticates users by 
    validating their credentials and generating a JWT (JSON Web Token) pair, 
    consisting of access and refresh tokens, for successful authentication.

    Attributes:
        serializer_class (CustomTokenObtainPairSerializer): The serializer used 
        to validate the user's credentials and generate the JWT tokens.

    Methods:
        post(request, *args, **kwargs):
            Handles the POST request for user login. It validates the user's 
            credentials using the CustomTokenObtainPairSerializer, and if valid, 
            returns a success response with JWT tokens. If the credentials are invalid, 
            it returns an error response.
    """

    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests for user login.

        This method takes the user's login credentials (typically username and password)
        from the request, validates them using the CustomTokenObtainPairSerializer, and 
        generates JWT access and refresh tokens if the credentials are correct.

        If the authentication is successful:
            - A JSON response is returned with a success message and the JWT tokens.
        
        If the authentication fails:
            - A JSON response is returned with an error message indicating invalid credentials.

        Args:
            request (HttpRequest): The HTTP request containing the user's login credentials.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: A DRF Response object containing either the JWT tokens on success
            or an error message on failure.

        Raises:
            ValidationError: If the provided credentials are invalid, the serializer
            raises a validation error.
        """
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):

            payload = utils.get_payload(
                request,
                message=f"User successfully loggedIn...",
                detail=serializer.validated_data,
            )
            return Response(data=payload, status=status.HTTP_200_OK)

        payload = utils.get_payload(
            request,
            message=f"Invalid Credentials.",
            detail=serializer.validated_data,
        )
        return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)


class CustomRefreshToken(TokenRefreshView):
    """
    API view for refreshing JWT tokens.

    This view allows clients to refresh their JWT access tokens by providing
    a valid refresh token. It extends Django REST Framework's TokenRefreshView 
    from the SimpleJWT package and uses a custom serializer, CustomTokenRefreshSerializer,
    to validate the provided refresh token and generate a new access token.

    Attributes:
        serializer_class (CustomTokenRefreshSerializer): The serializer used to 
        validate the refresh token and generate a new access token.

    Methods:
        post(request):
            Handles the POST request to refresh an access token. It validates
            the provided refresh token using the CustomTokenRefreshSerializer, and if valid,
            returns a new access token. If the refresh token is invalid, an error response is returned.
    """
    serializer_class = CustomTokenRefreshSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            payload = utils.get_payload(
                request,
                message=f"access token generated successfully.",
                detail=serializer.validated_data,
            )
            return Response(data=payload, status=status.HTTP_200_OK)

        payload = utils.get_payload(
            request,
            message=f"Invalid Token.",
            # detail=serializer.validated_data,
        )
        return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:

            return Response(status=status.HTTP_400_BAD_REQUEST)


class UsersAPIView(APIView):
    """
    API view for managing user data.

    This view handles various user-related operations, including fetching user data,
    creating new users, updating existing users, and deleting users. It uses JWT-based
    authentication and custom permissions to ensure that only authorized users can access
    these operations.

    Attributes:
        authentication_classes (list): Specifies the authentication method used (JWTAuthentication).
        permission_classes (list): Specifies the custom permissions required to access the view.
        createuser_serializer_class (CreateUserSerializer): Serializer class used for creating users.
        user_serializer_class (UserSerializer): Serializer class used for serializing user data.
        user_obj (UserManager): Manager for performing queries on the User model.

    Methods:
        get(request):
            Handles GET requests for retrieving user data, either a list of users
            or details of a specific user based on a slug.
        
        post(request):
            Handles POST requests for creating new users. Validates the input data
            and returns appropriate responses for success or error cases.
        
        patch(request):
            Handles PATCH requests for updating existing users. Partial updates are
            supported, and the user is identified via the provided slug.
        
        delete(request):
            Handles DELETE requests for deleting users. The users to delete are identified
            by their slug.
    """

    authentication_classes = [
        JWTAuthentication
    ]  # check for user is autnenticated or not.
    permission_classes = [CustomPermission]  # check for user has permissions or not

    createuser_serializer_class = CreateUserSerializer
    user_serializer_class = UserSerializer
    user_obj = User.objects

    def get(self, request):
        """
        Handle GET requests for retrieving users.

        This method retrieves either a list of users or the details of a specific user 
        based on the provided `slug` parameter. If no slug is provided, all users are 
        fetched, along with their roles using prefetching. The response is paginated.

        Args:
            request (HttpRequest): The HTTP request containing optional query parameters.

        Returns:
            Response: A paginated list of users or details of a single user. If the
            requested user or page is not found, appropriate error messages are returned.
        """

        # # Prefetch roles for each user and store them in the 'roles' attribute
        from leads.models import StudentLeads, ParentsInfo
        from locations.models import Address
        from info_bridge.models import DataBridge
        ParentsInfo.objects.all().delete()
        Address.objects.all().delete()
        StudentLeads.objects.all().delete()
        DataBridge.objects.all().delete()

        # print("Lead Count: ", lead_count)
        slug = request.GET.get("slug", None)
        if not slug:
            users_with_roles = User.objects.prefetch_related(
                Prefetch(
                    "related_user",  # Related name from UserRoleMapping
                    queryset=UserRoleMapping.objects.select_related("role").only(
                        "role__role_name"
                    ),
                    to_attr="roles",
                )
            ).order_by("-created_on")

            try:
                paginated_user_qs = pagination.paginate_queryset(users_with_roles, request)
            except NotFound:
                payload = utils.get_payload(
                    request,
                    detail=[],
                    message="Users List."
                )
                return Response(data=payload, status=status.HTTP_200_OK)    
            serialized_user_qs = UserListSerializer(paginated_user_qs, many=True).data
            payload = utils.get_payload(
                request,
                detail=serialized_user_qs,
                message="Users List.",
                extra_information=pagination.get_paginated_response(
                    data=serialized_user_qs
                ),
            )
            return Response(data=payload, status=status.HTTP_200_OK)

        else:
            try:
                user_info = self.user_obj.get(slug=slug)
                serialized_user_info = UserSerializer(user_info).data
                payload = utils.get_payload(
                    request, detail=serialized_user_info, message="User details."
                )
                return Response(data=payload, status=status.HTTP_200_OK)

            except User.DoesNotExist:
                payload = utils.get_payload(
                    request, detail={}, message="User doesn't exists."
                )
                return Response(data=payload, status=status.HTTP_404_NOT_FOUND)

            except (ValueError, ValidationError):
                payload = utils.get_payload(request, detail={}, message="Bad Request")
                return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)

            except Exception as e:
                print("UN-EXPECTED ERROR: ", e)
                payload = utils.get_payload(
                    request, detail={}, message="An Un-expected error occurse."
                )
                return Response(
                    data=payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    def post(self, request):
        """
        Handle POST requests for creating new users.

        This method takes the user data from the request, validates it using the 
        CreateUserSerializer, and creates a new user in the system if the validation
        is successful. In case of errors, appropriate error messages are returned.

        Args:
            request (HttpRequest): The HTTP request containing user data.

        Returns:
            Response: A success response with the user data on successful creation, or
            an error response for validation or other issues.
        """

        serialized_user_data = self.createuser_serializer_class(data=request.data)

        try:
            serialized_user_data.is_valid(raise_exception=True)
            serialized_user_data.save()

        except IntegrityError:
            payload = utils.get_payload(
                request, detail={}, message="related emal already exists."
            )
            return Response(data=payload, status=status.HTTP_409_CONFLICT)

        except Exception as e:
            payload = utils.get_payload(
                request, detail={}, message="An un-expected error occurse."
            )
            return Response(data=payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        payload = utils.get_payload(
            request, detail=request.data, message="User has been successfully created."
        )
        return Response(data=payload, status=status.HTTP_200_OK)

    def patch(self, request):
        """
        Handle PATCH requests for updating user data.

        This method updates an existing user's data. The user to be updated is identified
        using the `slug` field, and only the provided fields are updated.

        Args:
            request (HttpRequest): The HTTP request containing the updated user data and slug.

        Returns:
            Response: A success response if the update is successful, or an error response 
            if the user does not exist, the slug is missing, or other issues occur.
        """

        data = request.data
        slug = data.get("slug", None)

        if not slug:
            payload = utils.get_payload(request, message="slug field is missing.")
            return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_instance = self.user_obj.get(slug=slug)

            serialized_user_data = self.createuser_serializer_class(
                instance=user_instance, data=data, partial=True
            )
            serialized_user_data.is_valid(raise_exception=True)
            serialized_user_data.save()

        except User.DoesNotExist:
            payload = utils.get_payload(request, message="User doesn't exists.")
            return Response(data=payload, status=status.HTTP_404_NOT_FOUND)

        except IntegrityError:
            payload = utils.get_payload(
                request, detail={}, message="related emal already exists."
            )
            return Response(data=payload, status=status.HTTP_409_CONFLICT)

        payload = utils.get_payload(
            request, detail=request.data, message="User has been successfully updated."
        )
        return Response(data=payload, status=status.HTTP_200_OK)

    def delete(self, request):

        """
        Handle DELETE requests for deleting users.

        This method deletes one or more users identified by their slug(s) passed in the
        request. If the user(s) do not exist or if the slug is missing, appropriate
        error messages are returned.

        Args:
            request (HttpRequest): The HTTP request containing the slug(s) of users to be deleted.

        Returns:
            Response: A success response if the user(s) are successfully deleted, or an
            error response if the users do not exist or if an unexpected error occurs.
        """
        
        slug = request.DELETE.get("slug", [])
        if not slug:
            payload = utils.get_payload(request, message="Slug is required.")
            return Response(data=payload, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_qs = self.user_obj.filter(slug__in=slug)
            if not user_qs:
                payload = utils.get_payload(request, message="User doesn't exists.")
                return Response(data=payload, status=status.HTTP_404_NOT_FOUND)

            user_qs.delete()
            payload = utils.get_payload(request, message="User deleted.")
            return Response(data=payload, status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            payload = utils.get_payload(
                request, detail={}, message="An Un-expected error occurse."
            )
            return Response(data=payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
