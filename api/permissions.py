from rest_framework.permissions import BasePermission, SAFE_METHODS

class SoloLecturaOAdministrador(BasePermission):
    """
    Permite acceso de solo lectura (GET, HEAD, OPTIONS) a cualquier usuario,
    pero requiere autenticación + staff o superuser para escritura.
    """

    def has_permission(self, request, view):
        # Permitir acceso de solo lectura a cualquiera
        if request.method in SAFE_METHODS:
            return True
        # Solo los administradores pueden hacer POST/PUT/DELETE
        return request.user and request.user.is_authenticated and request.user.is_staff
