from rest_framework.permissions import BasePermission

ADMIN = "Admin"
SALES = "Sales User"
INVENTORY = "Inventory Manager"
ALL_ROLES = (ADMIN, SALES, INVENTORY)


def user_roles(user):
    if not getattr(user, "is_authenticated", False):
        return set()
    if not hasattr(user, "_role_cache"):
        user._role_cache = set(user.groups.values_list("name", flat=True))
        if user.is_superuser:
            user._role_cache.add(ADMIN)
    return user._role_cache


class HasAnyRole(BasePermission):
    allowed_roles = ()
    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        return bool(user_roles(request.user) & set(self.allowed_roles))


class IsAnyStaffRole(HasAnyRole):
    allowed_roles = ALL_ROLES


class IsAdmin(HasAnyRole):
    allowed_roles = (ADMIN,)


class IsAdminOrSales(HasAnyRole):
    allowed_roles = (ADMIN, SALES)


class IsAdminOrInventory(HasAnyRole):
    allowed_roles = (ADMIN, INVENTORY)


class IsOrderOwnerOrAdmin(BasePermission):
    message = "You can only act on your own orders."

    def has_object_permission(self, request, view, obj):
        roles = user_roles(request.user)
        if ADMIN in roles:
            return True
        return SALES in roles and obj.created_by_id == request.user.id