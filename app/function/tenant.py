from fastapi import HTTPException,status


def user_role_admin(current_user):
    if not hasattr(current_user, "role") or not current_user.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Current user role information is missing."
        )

    if current_user.role.user_role not in ['tenantowner', 'tenantadmin']:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"{current_user.user_name}, you don't have privilege to change Role. Please contact Admin!"
        )