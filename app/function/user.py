

from fastapi import HTTPException,status


def get_user_status(current_user):
  if not hasattr(current_user, "is_active") or not current_user.is_active:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail=f"Inactive user, Please contact your Admin {current_user.tenant.tenant_name}"
    )
    
  if not hasattr(current_user, "is_verified") or not current_user.is_verified:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail=f"user not verifed, Please contact your Admin {current_user.tenant.tenant_name}"
    )

58
