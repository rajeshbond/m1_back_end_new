from fastapi import status,HTTPException,Depends,APIRouter
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError


from .. import schemas,oauth2,models
from ..function import admin, backtable, user
from .. import utls
from ..database import get_db


router = APIRouter(
  prefix="/admin/v1",tags=['admin']
)

# functions for admin 

   

# Create Role Start here (created on 22.7.2025 by Rajesh Bondgilwar) --------------------------->
@router.post('/create-role',status_code=status.HTTP_201_CREATED,include_in_schema=False)
def admin_create_role(
  role:schemas.RoleCreate,
  db:Session = Depends(get_db),
  current_user: int = Depends(oauth2.get_current_user)):
  try: 
    admin.user_role_admin(current_user)
    user.get_user_status(current_user)
    user_role1 = role.user_role.lower()
    existing_role = db.query(models.UserRole).filter(models.UserRole.user_role == user_role1).first()
    if existing_role:
       raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"{user_role1} role already present Role Table ")
       
    
    new_role = models.UserRole(user_role = user_role1,created_by = current_user.id,updated_by = current_user.id)
    db.add(new_role)
    db.commit()
    db.refresh(new_role)

    return {"message":"sucessful","role":schemas.RoleOut.model_validate(new_role)}

   
  except HTTPException as he:
     raise he  
  except SQLAlchemyError as e:
     db.rollback()
     raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Database error: {str(e)}")
  except Exception as e:
    db.rollback()
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Internal server error{str(e)}")


# Create Role Ends <---------------------------------( rev 0.0 dt 22.7.2025 by Rajesh Bondgilwar)

# Create Role Start here (created on 22.7.2025 by Rajesh Bondgilwar) --------------------------->
@router.post('/change-role', status_code=status.HTTP_200_OK)
def admin_change_role(
    role: schemas.ChangeRole,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    try:
        if role.user_role.lower() == role.change_role.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"{role.change_role} is same as {role.user_role}")
        # ✅ Call the correct helper function
        user.get_user_status(current_user)
        admin.user_role_admin(current_user)

        # ✅ Check if role exists
        user_role1 = role.user_role.lower()
        existing_role = db.query(models.UserRole).filter(models.UserRole.user_role == user_role1).first()
        if not existing_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{user_role1} not present in Role Table"
            )
        existing_role.user_role = role.change_role.lower()
        existing_role.updated_by = current_user.id

        db.commit()
        db.refresh(existing_role)


        return {
            "message": "Successful",
            "change_role": schemas.RoleOut.model_validate(existing_role)
        }

    except HTTPException as he:
        raise he
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

# Create Role Ends <---------------------------------( rev 0.0 dt 22.7.2025 by Rajesh Bondgilwar)


# Create Tenant Start here (created on 22.7.2025 by Rajesh Bondgilwar) --------------------------->
@router.post('/create-tenant',status_code=status.HTTP_201_CREATED)
def admin_create_tenant(tenantAdmin:schemas.CreateAdminTenant,db:Session = Depends(get_db),current_user: int = Depends(oauth2.get_current_user)):
  try:
    tenant = tenantAdmin.tenant
    user_data = tenantAdmin.user
    # print(user_data)
    user.get_user_status(current_user)
    admin.user_role_admin(current_user)
    tenant.tenant_code = tenant.tenant_code.lower()
    role = 'tenantowner'
    exisiting_role = db.query(models.UserRole).filter(models.UserRole.user_role==role).first()
    # print(exisiting_role.id)
    if not exisiting_role:
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"{role} not found")
    existing_tenant = db.query(models.Tenant).filter(models.Tenant.tenant_code == tenant.tenant_code).first()
    
    if existing_tenant:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"{tenant.tenant_name} tenant already present Tenant Table ")
    tenant.tenant_code = tenant.tenant_code.lower()
    new_tenant = models.Tenant(**tenant.model_dump(),created_by = current_user.id,updated_by = current_user.id)
    
    # return tenant , user_data
    db.add(new_tenant)
    db.flush()
    # print(new_tenant.id)
    user_data.password = utls.hash(user_data.password)
    user_data.employee_id = utls.employee_code(user_data.employee_id,tenant.tenant_code)
    new_user = models.User(**user_data.model_dump(),tenant_id = new_tenant.id,role_id = exisiting_role.id,created_by = current_user.id,updated_by = current_user.id)

    db.add(new_user)
    db.flush()
    db.commit()
    
    #  db.refresh(new_tenant)
    return {"message":"sucessful","tenant":schemas.Tenantout.model_validate(new_tenant),"user":schemas.UserOut.model_validate(new_user)}
    
    pass
  except HTTPException as he:
     raise he
  except SQLAlchemyError as e:
     db.rollback()
     raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Database error: {str(e)}")
  except Exception as e:
    db.rollback()
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Internal server error{str(e)}")

# Create Tenant Ends <---------------------------------( rev 0.0 dt 22.7.2025 by Rajesh Bondgilwar)

# Change Password Start here (created on 22.7.2025 by Rajesh Bondgilwar) --------------------------->
@router.post('/change-password',status_code=status.HTTP_200_OK)
def change_password(changePassword:schemas.ChangePassword,db:Session = Depends(get_db),current_user: int = Depends(oauth2.get_current_user)):
  try:
    user.get_user_status(current_user)
    admin.user_role_admin(current_user)
    user_id = changePassword.employee_id
    user_data = db.query(models.User).filter(models.User.employee_id == user_id).first()
    if not user_data:
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")
    if not utls.verify(changePassword.old_password,user_data.password):
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Password not match, Please Enter correct Password ")
   
    user.get_user_status(user_data)
    user_data.password = utls.hash(changePassword.new_password)
    user_data.updated_by = current_user.id
    db.commit()
    db.refresh(user_data)
    return {"message":"Password Updated ","user":schemas.UserOut.model_validate(user_data)}
  except HTTPException as he:
    raise he
  except SQLAlchemyError as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Database error: {str(e)}")
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Internal server error{str(e)}")
     
# Chanege Password Ends <---------------------------------( rev 0.0 dt 22.7.2025 by Rajesh Bondgilwar)

# Reset Password Start here (created on 22.7.2025 by Rajesh Bondgilwar) --------------------------->
@router.post('/rest-password',status_code=status.HTTP_200_OK)
def rest_password(restPassword:schemas.ResetPassword,db:Session = Depends(get_db),current_user: int = Depends(oauth2.get_current_user)):
  try:
    user.get_user_status(current_user)
    admin.user_role_admin(current_user)
    user_id = restPassword.employee_id
    user_data = db.query(models.User).filter(models.User.employee_id == user_id).first()
    if not user_data:
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found") 
    user.get_user_status(user_data)
    user_data.password = utls.hash(restPassword.new_password)
    user_data.updated_by = current_user.id
    db.commit()
    db.refresh(user_data)
    return {"message":"Password Updated ","user":schemas.UserOut.model_validate(user_data)}
  except HTTPException as he:
    raise he
  except SQLAlchemyError as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Database error: {str(e)}")
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Internal server error{str(e)}")
     
# Rest Password Ends <---------------------------------( rev 0.0 dt 22.7.2025 by Rajesh Bondgilwar)

# Create User Start here (created on 22.7.2025 by Rajesh Bondgilwar) --------------------------->
@router.post("/admin-user",status_code=status.HTTP_201_CREATED)
def createUser(createUser:schemas.UserCreate,db:Session = Depends(get_db),current_user: int = Depends(oauth2.get_current_user)):
   
  try:
    admin.user_role_admin(current_user)
    user_exists = backtable.getUserByEmployeCode(utls.employee_code(createUser.employee_id,createUser.tenant_code),db)
    if user_exists:
       raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"User already exists {createUser.user_name}")
    user_email_exist = backtable.getUserByEmployeEmail(createUser.email,db)
    if user_email_exist:  
       raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"User already exists {createUser.email}")
    role_details = backtable.getRoleBycode(createUser.role,db)

    print(role_details.id)
    tenant_details = backtable.getTenantByCode(createUser.tenant_code,db)
  
    new_user = {
       "tenant_id":tenant_details.id,
       "role_id":role_details.id,
       "employee_id":utls.employee_code(createUser.employee_id,createUser.tenant_code),
       "user_name":createUser.user_name,
       "phone":createUser.phone,
       "email":createUser.email,
       "password":utls.hash(createUser.password),
       "created_by":current_user.id,
       "updated_by":current_user.id
    }
    user_data = models.User(**new_user)
    print(user_data)
    db.add(user_data)
    db.commit()
    db.refresh(user_data)
    return {"message":"User Created","user":schemas.UserOut.model_validate(user_data)}


    pass 
  except HTTPException as he:
    raise he
  except SQLAlchemyError as e:
     raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED,detail=f"SQL Server Error {str(e)}")
  except Exception as e:
     raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail= f"Internal Server Error {str(e)}")

# Create User Ends <---------------------------------( rev 0.0 dt 22.7.2025 by Rajesh Bondgilwar)
