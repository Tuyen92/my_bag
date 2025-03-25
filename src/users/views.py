from django.contrib.auth.models import Group, User
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import permissions, viewsets, status, mixins, views
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.exceptions import PermissionDenied

from companies.models import Company
from projects.models import Project, UserProjectRel
from projects.serializers import ProjectSerializer
from shared.permissions import IsAdminOrManager, IsAdmin, IsManager, IsSelf, IsSelfOrAdmin, IsSelfOrAdminOrManager
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    GroupSerializer,
    UserSerializer,
    ChangePasswordSerializer,
    UserCreationSerializer,
    CustomTokenObtainPairSerializer,
    CustomTokenRefreshSerializer,
    ResendOTPSerializer,
    OTPVerificationSerializer,
    ResetPassWithOTPSerializer
)
from .models import UserProfile
from .services import AuthService, EmailService


class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class CheckTokenExpiryView(views.APIView):
    """
    View to check if the access token has expired.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Check if the access token has expired
        """
        # Extract token from the Authorization header
        token = request.headers.get('Authorization').split(' ')[1]
        try:
            # Decode the access token using SimpleJWT's built-in method
            access_token = AccessToken(token)

            # Check if the token is expired
            if access_token.check_exp():
                return Response({"detail": "Token has expired."}, status=status.HTTP_401_UNAUTHORIZED)

            return Response({"detail": "Token is valid."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Override get_queryset to return users in the same company as the requesting user.
        """
        user = self.request.user  # Get the requesting user
        if user.is_authenticated:
            # Filter queryset to only include users in the same company
            return User.objects.filter(user_profile__company=user.user_profile.company)
        return User.objects.none()  # If the user isn't authenticated, return no results

    def get_serializer_context(self):
        # Add the request to the serializer context
        return {'request': self.request}

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Endpoint to retrieve the authenticated user's information.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdmin], url_path='add-employee') #, url_path='employees/add-employee')
    def add_employee(self, request, company_id=None):
        """
        Add a new employee to the company.
        Only accessible to company admins or managers.
        """
        # Check if the user is the admin or manager of the company
        company = get_object_or_404(Company, id=company_id)
        
        # Add the user creation logic here
        serializer = UserCreationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.save(company=company)
            return Response({"detail": "Employee added successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['put'], permission_classes=[IsSelfOrAdminOrManager], url_path='update-info')
    def update_user_info(self, request, pk=None, company_id=None):
        """
        Update user information (e.g., name, email).
        """
        user = self.get_object()

        # Ensure the permission check is passed
        self.check_object_permissions(request, user)

        serializer = self.get_serializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"detail": "User's informations are updated successfully."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsSelf], url_path='change-password')
    def change_password(self, request, pk=None):
        """
        Endpoint to change the password of the authenticated user.
        Only the user themselves can change their password.
        """
        user = self.get_object()

        # Ensure the permission check is passed
        self.check_object_permissions(request, user)

        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']

            # Check if the old password is correct
            if not user.check_password(old_password):
                return Response({"detail": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

            # Set the new password
            user.set_password(new_password)
            user.save()

            return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAdmin], url_path='update-role')
    def update_user_role(self, request, pk=None, company_id=None):
        """
        Update the group of a user based on their user ID.
        Only accessible to admins or managers.
        """
        user = get_object_or_404(User, pk=pk)

        # Validate the group name
        group_name = request.data.get('role')
        if not group_name:
            return Response(
                {"error": "Role name is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch the group object
        group = Group.objects.filter(name=group_name).first()
        if not group:
            return Response(
                {"error": f"Role '{group_name}' does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Update the user's group
        user.groups.clear()  # Clear existing groups
        user.groups.add(group)

        return Response(
            {"message": f"User '{user.username}' has been changed to role '{group_name}'."},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAdmin], url_path='delete')
    def soft_delete_user(self, request, pk=None, company_id=None):
        """
        Soft delete a user by setting `is_active` to False.
        Only accessible by admins.
        """
        # Fetch the user based on their user ID
        user = get_object_or_404(User, pk=pk)

        # Prevent soft-deleting an already inactive user
        if not user.is_active:
            return Response(
                {"error": f"User '{user.username}' is already deleted."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Soft delete the user
        user.is_active = False
        user.save()

        return Response(
            {"message": f"User '{user.username}' has been deleted."},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'], url_path='assigned-projects', permission_classes=[IsAdminOrManager])
    def get_assigned_projects(self, request, pk=None, company_id=None):
        """
        Retrieve projects are assigned to this user.
        """
        user = self.get_object()
        project_relations = user.assigned_users.all()  # Reverse relationship from User to UserProjectRel
        projects = [rel.project for rel in project_relations]  # Extract the Project objects
        serializer = ProjectSerializer(projects, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'], url_path='unassigned-projects', permission_classes=[IsAdminOrManager])
    def get_unassigned_projects(self, request, pk=None, company_id=None):
        """
        Retrieve projects are not assigned to this user.
        """
        user = self.get_object()
        company = Company.objects.get(id=company_id)
        project_relations = company.projects.all()

        # Get the IDs of projects already assigned to the user
        assigned_project_ids = user.assigned_users.values_list('project_id', flat=True)

        # Filter projects are not assigned to the user
        projects_lst = project_relations.exclude(id__in=assigned_project_ids)
        unassigned_projects = [project for project in projects_lst]

        # Serialize the unassigned projects
        serializer = ProjectSerializer(unassigned_projects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='assign-projects', permission_classes=[IsAdminOrManager])
    def assign_projects(self, request, pk=None, company_id=None):
        """
        Endpoint to assign a list of projects to a user.
        Only accessible to admins or managers of the company.
        """
        user = self.get_object()
        project_ids = request.data.get("project_ids", [])
        
        if not project_ids:
            return Response(
                {"detail": "No project IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Check if projects exist
                projects = Project.objects.filter(id__in=project_ids)
                if projects.count() != len(project_ids):
                    return Response({"detail": "One or more projects not found."}, status=status.HTTP_404_NOT_FOUND)

                # Create UserProjectRel instances for each user
                for assign_project in projects:
                    if assign_project.company != user.user_profile.company:
                        raise PermissionDenied(
                            f"Project {assign_project.name} does not belong to the same company as the user."
                        )
                    UserProjectRel.objects.get_or_create(user=user, project=assign_project)

                return Response(
                    {"detail": "Projects assigned to the user successfully."},
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='unassign-projects', permission_classes=[IsAdminOrManager])
    def unassign_projects(self, request, pk=None, company_id=None):
        """
        Endpoint to unassign a list of projects from a user.
        Only accessible to admins or managers of the company.
        """
        user = self.get_object()
        project_ids = request.data.get("project_ids", [])

        if not project_ids:
            return Response(
                {"detail": "No project IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                # Check if projects exist
                projects = Project.objects.filter(id__in=project_ids)
                if projects.count() != len(project_ids):
                    return Response(
                        {"detail": "One or more projects not found."},
                        status=status.HTTP_404_NOT_FOUND
                    )

                # Delete UserProjectRel instances for each user
                for assign_project in projects:
                    if user.user_profile.company != assign_project.company:
                        raise PermissionDenied(
                            f"Project {assign_project.name} does not belong to the same company as the user."
                        )
                    try:
                        user_project_rel = UserProjectRel.objects.get(
                            user=user, project=assign_project
                        )
                        user_project_rel.delete()
                    except UserProjectRel.DoesNotExist:
                        return Response(
                            {"detail": f"Project {assign_project.name} is not assigned to this user."},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                return Response(
                    {"detail": "Projects unassigned from the user successfully."},
                    status=status.HTTP_200_OK
                )

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all().order_by('name')
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserRegistrationViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    """
    A viewset to register a new user and create a new company.
    """
    # Allow unauthenticated access to the registration endpoint
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        """
        Handle user registration and company creation.
        """
        serializer = self.get_serializer(data=request.data)

        # Validate and create the user and company
        if serializer.is_valid():
            user = serializer.save()

            # Return success response with user and company information
            return Response(
                {
                    "message": "User and company created successfully",
                    "user_id": user.id,
                    "company_id": user.user_profile.company.id,
                },
                status=status.HTTP_201_CREATED
            )

        # Return validation errors if there are any
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendOTPView(APIView):
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            email = serializer.validated_data['email']

            # Generate and send OTP
            EmailService.send_otp_email(email)
            return Response({"message": "OTP sent successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            # Mark user as active after successful OTP verification
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            user.is_active = True
            user.save()

            return Response(
                {"message": "OTP verified successfully. Account is now active."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ResetPassWithOTPView(APIView):
    def post(self, request):
        serializer = ResetPassWithOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Reset user password after successful OTP verification
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = User.objects.get(email=email)
        user.set_password(password)
        user.save()

        return Response(
            {"message": "Reset password successfully."},
            status=status.HTTP_200_OK
        )


class UserLoginViewSet(viewsets.GenericViewSet, viewsets.ViewSet):
    """
    A viewset to allow user login into the application.
    """
    # Allow unauthenticated access to the registration endpoint
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    def create(self, request, *args, **kwargs):
        """
        Handle user login endpoint.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        remember_me = serializer.validated_data.get('remember_me', False)

        # Generate tokens with dynamic expiration based on "remember_me"
        tokens = AuthService.generate_tokens(user, remember_me=remember_me)

        # Serialize user data
        user_data = UserSerializer(user).data

        # Combine tokens and user data in the response
        response_data = {
            **tokens,
            "user": user_data,
        }

        return Response(response_data, status=status.HTTP_200_OK)


class LogoutViewSet(viewsets.GenericViewSet, viewsets.ViewSet):
    """
    A ViewSet to handle user logout by blacklisting the refresh token.
    """
    # Allow unauthenticated access to the registration endpoint
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"detail": "Logout successful."},
                status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {"detail": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST
            )


class ChangePasswordViewSet(viewsets.ViewSet):
    """
    ViewSet for changing the authenticated user's password.
    """
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request):
        """
        Handles password change requests for authenticated users.

        Validates the old password, ensures the new passwords match,
        and updates the user's password.
        """
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            # Set the new password
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()

            return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

