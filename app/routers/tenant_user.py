from fastapi import status,HTTPException,Depends,APIRouter
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.function import declare, user


from .. import schemas,oauth2,models
from ..function import admin, backtable,tenant,fetch_details
from .. import utls
from ..database import get_db


router = APIRouter(
  prefix="/user/v1",tags=['user']
)
# Change password Start here (created on 29.7.2025 by Rajesh Bondgilwar) --------------------------->

@router.post('/change-password',status_code=status.HTTP_200_OK)
def change_password(changePassword:schemas.UserChangePassword,db:Session = Depends(get_db),current_user: int = Depends(oauth2.get_current_user)):
  try:
    
    user.get_user_status(current_user)
    if changePassword.old_password == changePassword.new_password:
       raise HTTPException(status_code=status.HTTP_302_FOUND,detail=f"Same password cant be changed , Please provide diffrent password!!!")
    if utls.verify(changePassword.new_password,current_user.password):
       raise HTTPException(status_code=status.HTTP_302_FOUND,detail=f"Same password cant be changed , Please provide diffrent password!!!")
    
    current_user.password = utls.hash(changePassword.new_password)
    current_user.updated_by = current_user.id
    db.commit()
    db.refresh(current_user)
    return {"message":"Password Updated ","user":schemas.UserOut.model_validate(current_user)}

  except HTTPException as he:
    raise he
  except SQLAlchemyError as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Database error: {str(e)}")
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Internal server error{str(e)}")
     
# Chanege Password Ends <---------------------------------( rev 0.0 dt 29.7.2025 by Rajesh Bondgilwar)


# User Department final Start here (created on 29.7.2025 by Rajesh Bondgilwar) --------------------------->
@router.post('/user-department', status_code=status.HTTP_200_OK)
def user_department(
    userDepartment: schemas.UserDepartment,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    try:
        # 1. Validate user, tenant, role
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)

        # Extract tenant code from employee_code
        userTenantCode = utls.dividecode(userDepartment.employee_code)
        requested_tenant = backtable.getTenantByCode(userTenantCode, db)

        if userTenantCode != current_user.tenant.tenant_code:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User not authorised to create department for {requested_tenant.tenant_name}"
            )

        # 2. Normalize and remove duplicates using helper function
        df_input_departments = declare.remove_duplicates(userDepartment.department)
        if df_input_departments.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid departments provided"
            )

        # 3. Get tenant departments
        query = db.query(models.Department.department_name, models.Department.id).filter(
            models.Department.tenant_id == requested_tenant.id
        )
        df_tenant_departments = pd.read_sql(query.statement, db.bind)
        df_tenant_departments["department_name"] = df_tenant_departments["department_name"].str.strip().str.lower()

        # Rename tenant column to match 'operations'
        df_tenant_departments.rename(columns={"department_name": "operations"}, inplace=True)

        # 4. Validate input departments against tenant's departments
        df_valid = df_input_departments.merge(df_tenant_departments, on="operations", how="inner")
        df_invalid = df_input_departments[~df_input_departments["operations"].isin(df_valid["operations"])]

        if df_valid.empty:
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail=f"{df_input_departments['operations'].tolist()} ----> Departments don't exist for {current_user.tenant.tenant_name}"
            )

        # 5. Fetch the user
        requested_user = backtable.getUserByEmployeCode(userDepartment.employee_code, db)
        if not requested_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with employee code {userDepartment.employee_code} not found"
            )

        # 6. Get user's existing departments
        query_existing = db.query(models.DepartmentUser.department_id).filter(
            models.DepartmentUser.user_id == requested_user.id
        )
        df_existing_user_dept = pd.read_sql(query_existing.statement, db.bind)

        if df_existing_user_dept.empty:
            df_existing_user_dept = pd.DataFrame(columns=["department_id"])

        # 7. Filter out already assigned departments
        df_new = df_valid[~df_valid["id"].isin(df_existing_user_dept["department_id"])]
        df_already = df_valid[df_valid["id"].isin(df_existing_user_dept["department_id"])]

        if df_new.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All selected departments are already assigned to this user"
            )

        # 8. Bulk insert new departments
        df_new["tenant_id"] = requested_tenant.id
        df_new["user_id"] = requested_user.id
        df_new["created_by"] = current_user.id
        df_new["updated_by"] = current_user.id

        # Rename department_id column if needed
        df_new.rename(columns={"id": "department_id"}, inplace=True)

        # Convert DataFrame to list of dicts
        records = df_new[["tenant_id", "user_id", "department_id", "created_by", "updated_by"]].to_dict(orient="records")

        # Bulk insert
        db.bulk_insert_mappings(models.DepartmentUser, records)
        db.commit()

        return {
            "message": "Departments processed successfully",
            "new_departments": df_new["operations"].tolist(),
            "already_assigned": df_already["operations"].tolist(),
            "invalid_departments": df_invalid["operations"].tolist()
        }

    except HTTPException as he:
        raise he
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# User Department Final Ends here <---------------------------------( rev 0.0 dt 29.7.2025 by Rajesh Bondgilwar)
