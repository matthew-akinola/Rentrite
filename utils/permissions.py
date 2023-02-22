from rest_framework import permissions


class IsAgent(permissions.BasePermission):
    message = "Only users that are agent can access this endpoint"
    
    def has_permission(self, request, view):
        
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user.is_agent)
