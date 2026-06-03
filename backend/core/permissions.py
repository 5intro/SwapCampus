"""自定义权限类."""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrReadOnly(BasePermission):
    """仅允许资源拥有者进行写操作，其余人只读."""

    def has_object_permission(self, request, view, obj):
        # 安全方法（GET, HEAD, OPTIONS）允许所有人访问
        if request.method in SAFE_METHODS:
            return True
        # 写操作仅允许资源拥有者
        return obj.user == request.user


class IsOwner(BasePermission):
    """仅允许资源拥有者访问."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
