"""
Custom permissions for VoxPop.
"""
from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    """
    Permission that checks if user is a superuser (superadmin).
    Used for admin panel access.
    """
    message = 'Apenas superadministradores podem acessar esta área.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_superuser
        )


class IsTenantMember(permissions.BasePermission):
    """
    Permission that checks if user is a member of the current tenant.
    """
    message = 'Voce nao tem acesso a este tenant.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return False

        membership = request.user.get_membership(tenant)
        return membership is not None and membership.is_active


class IsTenantAdmin(permissions.BasePermission):
    """
    Permission that checks if user is an admin (owner or admin) of the tenant.
    """
    message = 'Apenas administradores podem realizar esta acao.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return False

        membership = request.user.get_membership(tenant)
        return membership is not None and membership.is_admin


class IsTenantOwner(permissions.BasePermission):
    """
    Permission that checks if user is the owner of the tenant.
    """
    message = 'Apenas o proprietario pode realizar esta acao.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return False

        membership = request.user.get_membership(tenant)
        return membership is not None and membership.is_owner


class CanEditTenant(permissions.BasePermission):
    """
    Permission that checks if user can edit (owner, admin, or operator).
    """
    message = 'Voce nao tem permissao para editar.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Read operations are allowed for all members
        if request.method in permissions.SAFE_METHODS:
            return True

        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return False

        membership = request.user.get_membership(tenant)
        return membership is not None and membership.can_edit


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission that allows owners to edit.
    Assumes the object has a 'created_by' field.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Check if object has created_by field
        created_by = getattr(obj, 'created_by', None)
        if created_by:
            return created_by == request.user

        return False
