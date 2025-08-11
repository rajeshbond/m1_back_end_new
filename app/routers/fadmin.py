from fastapi import APIRouter,Depends,status,HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError,IntegrityError
from .. import (utls,schemas,models)
from ..database import get_db


router = APIRouter(prefix="/fadmin",tags=["IntitalRun"])

@router.post('/runfirst',status_code=status.HTTP_201_CREATED)
def initaliseAdmin(setup:schemas.SetupSuperAdmin,db:Session = Depends(get_db)):
  try:

    
  
    role = setup.role
    tenant = setup.tenant
    user = setup.user
    # Role table


    role.user_role = role.user_role.lower()
    if role.user_role != "superadmin":
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Not authorized")

    existing_role = db.query(models.UserRole).filter(models.UserRole.user_role == role.user_role).first()
    if existing_role:
      raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"{role.user_role} already present")
    

    new_role = models.UserRole(**role.model_dump(),created_by = 1,updated_by =1 )
    db.add(new_role)
    db.flush()
    # -------------------------------------------------------------------------------
    # Tenant table
    tenant.tenant_code = tenant.tenant_code.lower()
    existing_tenant = db.query(models.Tenant).filter(models.Tenant.tenant_code == tenant.tenant_code).first()
    if existing_tenant:
      raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"{tenant.tenant_name} already present")
    
    new_tenant = models.Tenant(**tenant.model_dump(),created_by = 1,updated_by =1)
    db.add(new_tenant)
    db.flush()
    # -------------------------------------------------------------------------------
    # User table  
    existing_user = db.query(models.User).filter(models.User.employee_id == user.employee_id).first()
    if existing_user:
      raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"{user.user_name} already present for {existing_user.tenant.tenant_name}")

    user.password = utls.hash(user.password)
    user.employee_id = utls.employee_code(user.employee_id,new_tenant.tenant_code)
    new_user = models.User(**user.model_dump(),tenant_id = new_tenant.id,role_id = new_role.id,created_by = 1,updated_by =1 )
    db.add(new_user)
    db.flush()
  
    # -------------------------------------------------------------------------------
    db.commit()
    return {"message":"sucessful","role":schemas.RoleOut.model_validate(new_role),"tenant":schemas.Tenantout.model_validate(new_tenant),"user":schemas.UserOut.model_validate(new_user)}
  
  except IntegrityError as e: 
        db.rollback()
        err_msg = str(e.orig)

        # Customize messages for specific constraints
        if "tenant_email_key" in err_msg:
            detail = f"Tenant email '{user.email}' already exists."
        elif "tenant_tenant_name_key" in err_msg:
            detail = f"Tenant name '{user.tenant_name}' already exists."
        elif "uix_tenant_employee" in err_msg:
            detail = f"User with employee_id '{user.employee_id}' already exists in this tenant."
        elif "user_role_user_role_key" in err_msg:
            detail = f"Role '{user.role_id}' already exists."
        else:
            detail = "Integrity error occurred. Please check your input."

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )
  except HTTPException as he:
    raise he
  except SQLAlchemyError as e:
    db.rollback()
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Database error: {str(e)}")
  except Exception as e:
    db.rollback()
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpted Error: {str(e)}")