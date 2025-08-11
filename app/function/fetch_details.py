

from fastapi import HTTPException,status
from app import models


def user_details(user,db):
    user = db.query(models.user).filter(models.user.id == user.id).first()
    if not user :
        return None, None, None
    tenant = db.query(models.tenant).filter(models.tenant.id==user.tenant_id).first()
    if not tenant:
        return None,None,None
    user_role = db.query(models.role).filter(models.role.id == user.role_id).first()
    if not user_role:
        return None,None,None
    
    return user, tenant, user_role

def tenant_present(tenant_name,db):
    tenant= db.query(models.tenant).filter(models.tenant.tenant_name == tenant_name).first()
    if not tenant:
        return False
    
    return tenant

def get_user_status(current_user):
  if not hasattr(current_user, "is_active") or not current_user.is_active:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Inactive user, Please contact your Admin"
    )
    
  if not hasattr(current_user, "is_verified") or not current_user.is_verified:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="user not verifed, Please contact your Admin"
    )
