from fastapi import HTTPException,status
from sqlalchemy.exc import SQLAlchemyError
from .. import models

def getRoleBycode(role_code,db):
  try:
    role_code = role_code.lower()
    role_details = db.query(models.UserRole).filter(models.UserRole.user_role==role_code).first()
    if not role_details:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{role_code}, role detials not found.")
    return role_details
  except HTTPException as he:
    raise he
  except SQLAlchemyError as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"SQL Server Error {str(e)}")
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Internal Server Error {str(e)}")
  
def getRoleBycodeId(role_id,db):
  try:
    role_details = db.query(models.UserRole).filter(models.UserRole.id==role_id).first()
    if not role_details:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{role_id}, role detials not found.")
    return role_details
  except HTTPException as he:
    raise he
  except SQLAlchemyError as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"SQL Server Error {str(e)}")
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Internal Server Error {str(e)}")

  
def getTenantByCode(tenant_code,db):
  try:
    tenant_code = tenant_code.lower()
    # print(tenant_code)
    tenant_details = db.query(models.Tenant).filter(models.Tenant.tenant_code==tenant_code).first()
    # print(tenant_details.tenant_name)
    if not tenant_details:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{tenant_code}, Tenant not detials not found.")
    return tenant_details
  except HTTPException as he:
    raise he
  except SQLAlchemyError as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"SQL Server Error {str(e)}")
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Internal Server Error {str(e)}")
  
def getTenantByCodeId(tenant_id,db):
  try:
    tenant_details = db.query(models.Tenant).filter(models.Tenant.id==tenant_id).first()
    if not tenant_details:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{tenant_id}, role detials not found.")
    return tenant_details
  except HTTPException as he:
    raise he
  except SQLAlchemyError as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"SQL Server Error {str(e)}")
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Internal Server Error {str(e)}")
  
  

def getUserByEmployeCode(employee_id,db):
  try:
    user_details = db.query(models.User).filter(models.User.employee_id==employee_id).first()
    if not user_details:
      return None
    return user_details
  except HTTPException as he:
    raise he
  except SQLAlchemyError as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"SQL Server Error {str(e)}")
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Internal Server Error {str(e)}")
  
def getUserByEmployeEmail(employee_email,db):
  try:
    user_details = db.query(models.User).filter(models.User.email==employee_email).first()
    if not user_details:
      return None
    return user_details
  except HTTPException as he:
    raise he
  except SQLAlchemyError as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"SQL Server Error {str(e)}")
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Internal Server Error {str(e)}")
  

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