from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Allows access only to users with role='admin'.
    """
    message = 'You do not have permission. Admin access required.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'admin'
        )


class IsStudent(BasePermission):
    """
    Allows access only to users with role='student'.
    """
    message = 'You do not have permission. Student access required.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'student'
        )


class IsAdminOrStudent(BasePermission):
    """
    Allows access to both admins and students.
    Used for endpoints where both roles can read
    but the view itself filters what each sees.
    """
    message = 'Authentication required.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['admin', 'student']
        )