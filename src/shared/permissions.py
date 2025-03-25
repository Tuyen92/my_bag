from django.contrib.auth.models import User
from rest_framework.permissions import BasePermission

from projects.models import UserProjectRel, Project
from companies.models import Company


class IsAdmin(BasePermission):
    """
    Custom permission to check if the user is admin
    of the company that the object belong to.
    """
    def has_object_permission(self, request, view, obj):
        # Check if the user is authenticated and belongs to 'Admin' group
        if not request.user.is_authenticated:
            return False
        
        if isinstance(obj, User):
            company = obj.user_profile.company
        elif isinstance(obj, Project):
            company = obj.company
        elif isinstance(obj, Company):
            company = obj
        
        # Check if the user is part of the 'Admin' group
        return (request.user.groups.filter(name="Admin").exists() \
                and request.user.user_profile.company == company)
    
class IsManager(BasePermission):
    """
    Custom permission to check if the user is manager
    of the company that the object belong to.
    """
    def has_object_permission(self, request, view, obj):
        # Check if the user is authenticated and belongs to 'Manager' group
        if not request.user.is_authenticated:
            return False
        
        if isinstance(obj, User):
            company = obj.user_profile.company
        elif isinstance(obj, Project):
            company = obj.company
        else: # isinstance(obj, Company):
            company = obj
        
        # Check if the user is part of the 'Manager' group
        return (request.user.groups.filter(name="Manager").exists() \
                and request.user.user_profile.company == company)

class IsSelf(BasePermission):
    """
    Custom permission to allow users to change their own password only.
    """
    def has_object_permission(self, request, view, obj):

        if isinstance(obj, User):
            user = obj
        else:
            user = obj.created_by

        # Users can only change their own password
        return request.user == user
    
class IsAssigned(BasePermission):
    """
    Custom permission to check if the user is assigned
    to the project
    """
    def has_permission(self, request, view):
        # Check if the user is authenticated and belongs to 'Admin' group
        user = request.user
        if not user.is_authenticated:
            return False
        
        # If it's a detail view, check if the user is assigned to the project
        if view.detail:
            project_id = view.kwargs.get("pk")
            if project_id and \
                UserProjectRel.objects.filter(user=user, project_id=project_id).exists():
                return True

        return False


class IsAdminOrManager(BasePermission):
    """
    Custom permission to allow access only to company admins or managers.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False

        is_admin_permission = IsAdmin().has_object_permission(request, view, obj)
        is_manager_permission = IsManager().has_object_permission(request, view, obj)

        # Grant access if either permission allows access
        return is_admin_permission or is_manager_permission
    

class IsAdminManagerOrAssigned(BasePermission):
    """
    Custom permission to allow access only to:
    - Admins
    - Managers
    - Users assigned to the project via UserProjectRel
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False

        is_admin_permission = IsAdmin().has_object_permission(request, view, obj)
        is_manager_permission = IsManager().has_object_permission(request, view, obj)
        is_assigned_permission = IsAssigned().has_permission(request, view)

        # Grant access if either permission allows access
        return is_assigned_permission or is_admin_permission or is_manager_permission

class IsSelfOrAdminOrManager(BasePermission):
    """
    Custom permission to check if the user is either himself/herself 
    or an Admin or a Manager of the company that the object belongs to.
    """
    def has_object_permission(self, request, view, obj):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # Reuse the logic from IsAdmin and IsManager permission
        is_self_permission = IsSelf().has_object_permission(request, view, obj)
        is_admin_permission = IsAdmin().has_object_permission(request, view, obj)
        is_manager_permission = IsManager().has_object_permission(request, view, obj)

        # Grant access if either permission allows access
        return is_self_permission or is_admin_permission or is_manager_permission
    
class IsSelfOrAdmin(BasePermission):
    """
    Custom permission to check if the user is either himself/herself 
    or an Admin of the company that the object belongs to.
    """
    def has_object_permission(self, request, view, obj):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # Reuse the logic from IsAdmin and IsManager permission
        is_self_permission = IsSelf().has_object_permission(request, view, obj)
        is_admin_permission = IsAdmin().has_object_permission(request, view, obj)

        # Grant access if either permission allows access
        return is_self_permission or is_admin_permission
