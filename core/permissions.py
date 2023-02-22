from rest_framework import permissions


class IsOwner(permissions.BasePermission):

    message = "Only apartment owners/agents can make changes to their apartments"

    def has_permission(self, request, view):
        return bool(
            request.method in permissions.SAFE_METHODS
            or request.user
            and request.user.is_authenticated
        ) # Equivalent to IsAuthenticated or ReadOnly

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        try:
            return obj.agent == request.user
        except:
            # In a case when a user object is the instance to be checked
            return obj == request.user


class IsFileOwner(IsOwner):
    """
    This permission checks for changes to pictures and media of an apartment
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.apartment.agent == request.user
