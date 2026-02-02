"""
NeuroLens Permissions Module

Role-based access control (RBAC) system.
"""

from enum import Enum
from functools import wraps
from typing import Callable

from fastapi import HTTPException, status


class Role(str, Enum):
    """User roles for RBAC."""
    
    ADMIN = "admin"
    OWNER = "owner"
    MEMBER = "member"
    VIEWER = "viewer"


class Permission(str, Enum):
    """Granular permissions."""
    
    # User permissions
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    
    # Organization permissions
    ORG_READ = "org:read"
    ORG_WRITE = "org:write"
    ORG_DELETE = "org:delete"
    ORG_MANAGE_MEMBERS = "org:manage_members"
    
    # Dataset permissions
    DATASET_READ = "dataset:read"
    DATASET_WRITE = "dataset:write"
    DATASET_DELETE = "dataset:delete"
    
    # Model permissions
    MODEL_READ = "model:read"
    MODEL_WRITE = "model:write"
    MODEL_DEPLOY = "model:deploy"
    
    # Inference permissions
    INFERENCE_RUN = "inference:run"
    INFERENCE_BATCH = "inference:batch"
    
    # Admin permissions
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
    ADMIN_MANAGE_USERS = "admin:manage_users"
    ADMIN_MANAGE_ORGS = "admin:manage_orgs"


# Role to permissions mapping
ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.ADMIN: set(Permission),  # All permissions
    Role.OWNER: {
        Permission.USER_READ,
        Permission.USER_WRITE,
        Permission.ORG_READ,
        Permission.ORG_WRITE,
        Permission.ORG_MANAGE_MEMBERS,
        Permission.DATASET_READ,
        Permission.DATASET_WRITE,
        Permission.DATASET_DELETE,
        Permission.MODEL_READ,
        Permission.MODEL_WRITE,
        Permission.MODEL_DEPLOY,
        Permission.INFERENCE_RUN,
        Permission.INFERENCE_BATCH,
    },
    Role.MEMBER: {
        Permission.USER_READ,
        Permission.ORG_READ,
        Permission.DATASET_READ,
        Permission.DATASET_WRITE,
        Permission.MODEL_READ,
        Permission.INFERENCE_RUN,
    },
    Role.VIEWER: {
        Permission.USER_READ,
        Permission.ORG_READ,
        Permission.DATASET_READ,
        Permission.MODEL_READ,
        Permission.INFERENCE_RUN,
    },
}


def has_permission(role: Role, permission: Permission) -> bool:
    """Check if a role has a specific permission."""
    return permission in ROLE_PERMISSIONS.get(role, set())


def has_any_permission(role: Role, permissions: list[Permission]) -> bool:
    """Check if a role has any of the specified permissions."""
    role_perms = ROLE_PERMISSIONS.get(role, set())
    return any(p in role_perms for p in permissions)


def has_all_permissions(role: Role, permissions: list[Permission]) -> bool:
    """Check if a role has all of the specified permissions."""
    role_perms = ROLE_PERMISSIONS.get(role, set())
    return all(p in role_perms for p in permissions)


def get_role_permissions(role: Role) -> set[Permission]:
    """Get all permissions for a role."""
    return ROLE_PERMISSIONS.get(role, set())


def require_permission(permission: Permission):
    """
    Decorator to require a specific permission.
    
    Usage:
        @require_permission(Permission.DATASET_WRITE)
        async def create_dataset(current_user: User):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current_user from kwargs
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )
            
            user_role = Role(current_user.role)
            if not has_permission(user_role, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission.value}",
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(min_role: Role):
    """
    Decorator to require a minimum role level.
    
    Role hierarchy: ADMIN > OWNER > MEMBER > VIEWER
    """
    role_hierarchy = [Role.VIEWER, Role.MEMBER, Role.OWNER, Role.ADMIN]
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )
            
            user_role = Role(current_user.role)
            user_level = role_hierarchy.index(user_role)
            min_level = role_hierarchy.index(min_role)
            
            if user_level < min_level:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Minimum role required: {min_role.value}",
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class PermissionChecker:
    """
    Permission checker for use in FastAPI dependencies.
    
    Usage:
        @router.get("/datasets")
        async def list_datasets(
            current_user: User = Depends(get_current_user),
            _: bool = Depends(PermissionChecker(Permission.DATASET_READ)),
        ):
            ...
    """
    
    def __init__(self, *permissions: Permission, require_all: bool = True):
        self.permissions = permissions
        self.require_all = require_all
    
    async def __call__(self, current_user) -> bool:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )
        
        user_role = Role(current_user.role)
        
        if self.require_all:
            has_perms = has_all_permissions(user_role, list(self.permissions))
        else:
            has_perms = has_any_permission(user_role, list(self.permissions))
        
        if not has_perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        
        return True
