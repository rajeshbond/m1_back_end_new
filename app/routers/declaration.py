from typing import List
from fastapi import status,HTTPException,Depends,APIRouter
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError


from .. import schemas,oauth2,models
from ..function import admin, backtable,tenant,fetch_details,user,shifts_fn,declare
from .. import utls
from ..database import get_db


router = APIRouter(
  prefix="/declaration/v1",tags=['setup']
)


@router.post("/operation", status_code=status.HTTP_201_CREATED)
def create_operations(
    operation_data: schemas.TenantOperation,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    try:
        # <---------- 1. Validate user, tenant, role ---------->
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)

        requested_tenant = backtable.getTenantByCode(operation_data.tenant_code, db)
        if operation_data.tenant_code != current_user.tenant.tenant_code:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not Authorised to create Operation for {requested_tenant.tenant_name}"
            )

        # <---------- 2. Remove duplicates from input ---------->
        unique_operations = declare.remove_duplicates(operation_data.operation)
        # unique_operations['operations'] = unique_operations['operations'].str.strip().str.lower()

        # <---------- 3. Fetch existing operations from DB ---------->
        existing_ops = db.query(models.Operation.operation_name).filter(
            models.Operation.tenant_id == current_user.tenant_id
        ).all()

        # Convert DB results to DataFrame (normalize to lowercase for comparison)
        df_existing = pd.DataFrame(existing_ops, columns=["operation_name"])
        df_existing['operation_name'] = df_existing['operation_name'].str.strip().str.lower()

        # <---------- 4. Filter only new operations ---------->
        df_unique = unique_operations[~unique_operations['operations'].isin(df_existing['operation_name'])].copy()

        if df_unique.empty:
            raise HTTPException(
                status_code=400,
                detail=f"{unique_operations['operations'].tolist()} already present, No new operations to add"
            )

        # <---------- 5. Add metadata columns ---------->
        df_unique['tenant_id'] = requested_tenant.id
        df_unique['created_by'] = current_user.id
        df_unique['updated_by'] = current_user.id
        df_unique.rename(columns={'operations': 'operation_name'}, inplace=True)

        # <---------- 6. Bulk insert ---------->
        db.bulk_insert_mappings(
            models.Operation,
            df_unique.to_dict(orient='records')
        )
        db.commit()

        return {
            "status": "success",
            "inserted_operations": df_unique['operation_name'].tolist()
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
# Operation Start  Ends <---------------------------------( rev 0.0 dt 30.7.2025 by Rajesh Bondgilwar)


# Department Start here (created on 2.8.2025 by Rajesh Bondgilwar) --------------------------->
@router.post("/department", status_code=status.HTTP_201_CREATED)
def create_department(
    payload: schemas.TenantDepartment,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    try:
        # 1. Validate user, tenant, role
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)
        requested_tenant = backtable.getTenantByCode(payload.tenant_code, db)

        if payload.tenant_code != current_user.tenant.tenant_code:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User not authorised to create department for {requested_tenant.tenant_name}"
            )

        # 2. Remove duplicates from input and normalize
        # unique_departments = list(set(dept.strip().lower() for dept in payload.department))
        unique_departments = declare.remove_duplicates(payload.department)
        # print(unique_departments['operations'])

        # 3. Fetch existing departments from DB
        existing_departments = db.query(models.Department.department_name).filter(
            models.Department.tenant_id == requested_tenant.id
        ).all()

        # Convert DB results to DataFrame (normalize for comparison)
        df_existing = pd.DataFrame(existing_departments, columns=["department_name"])
        df_existing["department_name"] = df_existing["department_name"].str.strip().str.lower()

        # 4. Convert unique input to DataFrame
        df_unique = pd.DataFrame(unique_departments, columns=["department_name"])

        # Filter only new departments (vectorized using pandas)
        df_unique = unique_departments[~unique_departments["operations"].isin(df_existing["department_name"])].copy()

        if df_unique.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All provided departments already exist. No new department to add."
            )

        # 5. Add metadata columns
        df_unique["tenant_id"] = requested_tenant.id
        df_unique["created_by"] = current_user.id
        df_unique["updated_by"] = current_user.id
        df_unique.rename(columns={'operations': 'department_name'}, inplace=True)
        # 6. Bulk insert into DB
        db.bulk_insert_mappings(
            models.Department,
            df_unique.to_dict(orient="records")
        )
        db.commit()

        return {
            "status": "success",
            "inserted_departments": df_unique["department_name"].tolist()
        }

    except HTTPException as he:
        raise he
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SQL Server Error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(e)}"
        )

# Department Ends here <---------------------------------( rev 0.0 dt 2.8.2025 by Rajesh Bondgilwar)


# Defect Start here (created on 2.8.2025 by Rajesh Bondgilwar) --------------------------->
@router.post("/defect", status_code=status.HTTP_201_CREATED)
def create_defect(
    payload: schemas.TenantDefect,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    try:
        # 1. Validate user, tenant, role
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)
        requested_tenant = backtable.getTenantByCode(payload.tenant_code, db)

        if payload.tenant_code != current_user.tenant.tenant_code:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User not authorised to create defects for {requested_tenant.tenant_name}"
            )

        # 2. Remove duplicates from input and normalize
        unique_defect = declare.remove_duplicates(payload.defect)  # DataFrame with 'operations'
        # print(unique_defect["operations"])

        # 3. Fetch existing defects from DB
        existing_defects = db.query(models.Defect.defect_name).filter(
            models.Defect.tenant_id == requested_tenant.id
        ).all()

        # Convert DB results to DataFrame
        df_existing = pd.DataFrame(existing_defects, columns=["defect_name"])
        df_existing["defect_name"] = df_existing["defect_name"].str.strip().str.lower()

        # 4. Filter only new defects
        df_unique = unique_defect[~unique_defect["operations"].isin(df_existing["defect_name"])].copy()

        if df_unique.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All provided defects already exist. No new defect to add."
            )

        # 5. Add metadata columns
        df_unique["tenant_id"] = requested_tenant.id
        df_unique["created_by"] = current_user.id
        df_unique["updated_by"] = current_user.id
        df_unique.rename(columns={"operations": "defect_name"}, inplace=True)

        # 6. Bulk insert into DB
        db.bulk_insert_mappings(
            models.Defect,
            df_unique.to_dict(orient="records")
        )
        db.commit()

        return {
            "status": "success",
            "inserted_defects": df_unique["defect_name"].tolist()
        }

    except HTTPException as he:
        raise he
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SQL Server Error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(e)}"
        )

# Department Ends here <---------------------------------( rev 0.0 dt 2.8.2025 by Rajesh Bondgilwar)

# Defect Start here (created on 2.8.2025 by Rajesh Bondgilwar) --------------------------->
@router.post("/down-time", status_code=status.HTTP_201_CREATED)
def create_downTime(
    payload: schemas.TenantDownTime,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    try:
        # 1. Validate user, tenant, role
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)
        requested_tenant = backtable.getTenantByCode(payload.tenant_code, db)

        if payload.tenant_code != current_user.tenant.tenant_code:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User not authorised to create defects for {requested_tenant.tenant_name}"
            )

        # 2. Remove duplicates from input and normalize
        unique_defect = declare.remove_duplicates(payload.down_time)  # DataFrame with 'operations'
        # print(unique_defect["operations"])

        # 3. Fetch existing defects from DB
        existing_defects = db.query(models.DownTime.downtime_name).filter(
            models.DownTime.tenant_id == requested_tenant.id
        ).all()

        # Convert DB results to DataFrame
        df_existing = pd.DataFrame(existing_defects, columns=["defect_name"])
        df_existing["defect_name"] = df_existing["defect_name"].str.strip().str.lower()

        # 4. Filter only new defects
        df_unique = unique_defect[~unique_defect["operations"].isin(df_existing["defect_name"])].copy()

        if df_unique.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All provided defects already exist. No new defect to add."
            )

        # 5. Add metadata columns
        df_unique["tenant_id"] = requested_tenant.id
        df_unique["created_by"] = current_user.id
        df_unique["updated_by"] = current_user.id
        df_unique.rename(columns={"operations": "downtime_name"}, inplace=True)

        # 6. Bulk insert into DB
        db.bulk_insert_mappings(
            models.DownTime,
            df_unique.to_dict(orient="records")
        )
        db.commit()

        return {
            "status": "success",
            "inserted_downtTime": df_unique["downtime_name"].tolist()
        }

    except HTTPException as he:
        raise he
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SQL Server Error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(e)}"
        )

# Department Ends here <---------------------------------( rev 0.0 dt 2.8.2025 by Rajesh Bondgilwar)

# -----------------------------------------Operation - department start here ---------------->

@router.post("/operation-department", status_code=status.HTTP_201_CREATED)
def create_operations_with_departments(
    payload: schemas.TenantOperationDepartment,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    try:
        # 1. Validate user and tenant
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)
        requested_tenant = backtable.getTenantByCode(payload.tenant_code, db)

        if payload.tenant_code != current_user.tenant.tenant_code:
            raise HTTPException(
                status_code=403,
                detail=f"User not authorised to create operations for {requested_tenant.tenant_name}"
            )

        # 2. Fetch all departments for tenant and map by name
        tenant_departments = db.query(models.Department).filter(
            models.Department.tenant_id == requested_tenant.id
        ).all()
        dept_name_to_id = {
            d.department_name.strip().lower(): d.id for d in tenant_departments
        }

        # 3. Normalize and map input to operation-department pairs
        operations_input = []
        for entry in payload.operations:
            op_name = entry.operation_name.strip().lower()
            for dept_name in entry.department_names:
                norm_dept = dept_name.strip().lower()
                if norm_dept not in dept_name_to_id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Department '{dept_name}' not found for tenant {payload.tenant_code}"
                    )
                operations_input.append({
                    "operation_name": op_name,
                    "department_id": dept_name_to_id[norm_dept]
                })

        df_ops = pd.DataFrame(operations_input)

        # 4. Fetch existing operation names
        existing_ops = db.query(models.Operation.operation_name).filter(
            models.Operation.tenant_id == requested_tenant.id
        ).all()
        existing_op_names = {name[0].strip().lower() for name in existing_ops}

        # 5. Insert new operations
        new_ops = df_ops[~df_ops["operation_name"].isin(existing_op_names)]["operation_name"].drop_duplicates()
        new_ops_records = [
            models.Operation(
                tenant_id=requested_tenant.id,
                operation_name=name,
                created_by=current_user.id,
                updated_by=current_user.id
            )
            for name in new_ops
        ]
        if new_ops_records:
            db.bulk_save_objects(new_ops_records)
            db.flush()

        # 6. Get all operation IDs
        all_operations = db.query(models.Operation).filter(
            models.Operation.tenant_id == requested_tenant.id
        ).all()
        op_name_to_id = {op.operation_name.strip().lower(): op.id for op in all_operations}

        # 7. Fetch existing operation-department mappings
        existing_links = db.query(
            models.Operation.operation_name,
            models.OperationDepartment.department_id
        ).join(models.OperationDepartment).filter(
            models.Operation.tenant_id == requested_tenant.id
        ).all()
        df_existing_links = pd.DataFrame(existing_links, columns=["operation_name", "department_id"])
        df_existing_links["operation_name"] = df_existing_links["operation_name"].str.strip().str.lower()

        # 8. Prepare new operation-department mappings
        df_ops["operation_id"] = df_ops["operation_name"].map(op_name_to_id)
        df_ops["tenant_id"] = requested_tenant.id
        df_ops["created_by"] = current_user.id
        df_ops["updated_by"] = current_user.id

        # 9. Remove duplicates
        df_unique = df_ops.merge(df_existing_links, how="left", indicator=True)
        df_unique = df_unique[df_unique["_merge"] == "left_only"].drop(columns=["_merge"])

        if df_unique.empty:
            raise HTTPException(
                status_code=400,
                detail="All provided operation-department mappings already exist."
            )

        db.bulk_insert_mappings(
            models.OperationDepartment,
            df_unique[["tenant_id", "operation_id", "department_id", "created_by", "updated_by"]].to_dict(orient="records")
        )
        db.commit()

        return {
            "status": "success",
            "inserted": df_unique[["operation_name", "department_id"]].to_dict(orient="records")
        }

    except HTTPException as he:
        raise he
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

# <--------------Operation departments Ends Here-------------------------------

# -------------------------Defect Departments Starts Here --------------------->

# @router.post("/defct-department", status_code=status.HTTP_201_CREATED)
# def create_defect_with_departments(
#     payload: schemas.TenantDefectDepartment,
#     db: Session = Depends(get_db),
#     current_user: int = Depends(oauth2.get_current_user)
# ):
#     try:
#         # 1. Validate user and tenant
#         user.get_user_status(current_user)
#         tenant.user_role_admin(current_user)
#         requested_tenant = backtable.getTenantByCode(payload.tenant_code, db)

#         if payload.tenant_code != current_user.tenant.tenant_code:
#             raise HTTPException(
#                 status_code=403,
#                 detail=f"User not authorised to create operations for {requested_tenant.tenant_name}"
#             )

#         # 2. Fetch all departments for tenant and map by name
#         tenant_departments = db.query(models.Department).filter(
#             models.Department.tenant_id == requested_tenant.id
#         ).all()
#         dept_name_to_id = {
#             d.department_name.strip().lower(): d.id for d in tenant_departments
#         }

#         # 3. Normalize and map input to operation-department pairs
#         defects_input = []
#         for entry in payload.defect:
#             defect_name = entry.defect_name.strip().lower()
#             for dept_name in entry.department_names:
#                 norm_dept = dept_name.strip().lower()
#                 if norm_dept not in dept_name_to_id:
#                     raise HTTPException(
#                         status_code=400,
#                         detail=f"Department '{dept_name}' not found for tenant {payload.tenant_code}"
#                     )
#                 defects_input.append({
#                     "defec_name": defect_name,
#                     "department_id": dept_name_to_id[norm_dept]
#                 })

#         df_ops = pd.DataFrame(defects_input)

#         # 4. Fetch existing operation names
#         existing_defects = db.query(models.Defect.defect_name).filter(
#             models.Defect.tenant_id == requested_tenant.id
#         ).all()
#         existing_defect_names = {name[0].strip().lower() for name in existing_defects}

#         # 5. Insert new operations
#         new_defects = df_ops[~df_ops["defect_name"].isin(existing_defect_names)]["defect_name"].drop_duplicates()
#         new_defects_records = [
#             models.Defect(
#                 tenant_id=requested_tenant.id,
#                 defect_name=name,
#                 created_by=current_user.id,
#                 updated_by=current_user.id
#             )
#             for name in new_defects
#         ]
#         if new_defects_records:
#             db.bulk_save_objects(new_defects_records)
#             db.flush()

#         # 6. Get all operation IDs
#         all_defetcts = db.query(models.Defect).filter(
#             models.Defect.tenant_id == requested_tenant.id
#         ).all()
#         defect_name_to_id = {op.defect_name.strip().lower(): op.id for op in all_defetcts}

#         # 7. Fetch existing operation-department mappings
#         existing_links = db.query(
#             models.Defect.defect_name,
#             models.OperationDepartment.department_id
#         ).join(models.OperationDepartment).filter(
#             models.Defect.tenant_id == requested_tenant.id
#         ).all()
#         df_existing_links = pd.DataFrame(existing_links, columns=["defect_name", "department_id"])
#         df_existing_links["defect_name"] = df_existing_links["defect_name"].str.strip().str.lower()

#         # 8. Prepare new operation-department mappings
#         df_ops["defect_id"] = df_ops["defect_name"].map(defect_name_to_id)
#         df_ops["tenant_id"] = requested_tenant.id
#         df_ops["created_by"] = current_user.id
#         df_ops["updated_by"] = current_user.id

#         # 9. Remove duplicates
#         df_unique = df_ops.merge(df_existing_links, how="left", indicator=True)
#         df_unique = df_unique[df_unique["_merge"] == "left_only"].drop(columns=["_merge"])

#         if df_unique.empty:
#             raise HTTPException(
#                 status_code=400,
#                 detail="All provided operation-department mappings already exist."
#             )

#         db.bulk_insert_mappings(
#             models.DefectDepartment,
#             df_unique[["tenant_id", "defect_id", "department_id", "created_by", "updated_by"]].to_dict(orient="records")
#         )
#         db.commit()

#         return {
#             "status": "success",
#             "inserted": df_unique[["defect_name", "department_id"]].to_dict(orient="records")
#         }

#     except HTTPException as he:
#         raise he
#     except SQLAlchemyError as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=500,
#             detail=f"Database error: {str(e)}"
#         )
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=500,
#             detail=f"Internal server error: {str(e)}"
#         )

@router.post("/defct-department", status_code=status.HTTP_201_CREATED)
def create_defect_with_departments(
    payload: schemas.TenantDefectDepartment,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    try:
        # 1. Validate user and tenant
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)
        requested_tenant = backtable.getTenantByCode(payload.tenant_code, db)

        if payload.tenant_code != current_user.tenant.tenant_code:
            raise HTTPException(
                status_code=403,
                detail=f"User not authorised to create defects for {requested_tenant.tenant_name}"
            )

        # 2. Fetch tenant departments and map to IDs
        tenant_departments = db.query(models.Department).filter(
            models.Department.tenant_id == requested_tenant.id
        ).all()

        dept_df = pd.DataFrame(
            [(d.department_name.strip().lower(), d.id) for d in tenant_departments],
            columns=["department_name", "department_id"]
        )

        # 3. Normalize and explode payload into defect-department pairs
        # Convert Pydantic models to dicts for DataFrame
        try:
            payload_df = pd.DataFrame([d.dict() for d in payload.defect])  # Pydantic v1
        except AttributeError:
            payload_df = pd.DataFrame([d.model_dump() for d in payload.defect])  # Pydantic v2

        # Ensure department_names is always a list
        payload_df["department_names"] = payload_df["department_names"].apply(
            lambda x: [x] if isinstance(x, str) else x
        )

        # Explode department_names
        payload_df = payload_df.explode("department_names")

        # Explode defect_names
        payload_df = payload_df.explode("defect_names")

        # Normalize strings
        payload_df["department_name"] = payload_df["department_names"].str.strip().str.lower()
        payload_df["defect_name"] = payload_df["defect_names"].str.strip().str.lower()

        df_input = payload_df[["department_name", "defect_name"]].drop_duplicates()

        # 4. Validate department names
        df_input = df_input.merge(dept_df, on="department_name", how="left")
        if df_input["department_id"].isnull().any():
            missing_depts = df_input.loc[df_input["department_id"].isnull(), "department_name"].unique()
            raise HTTPException(
                status_code=400,
                detail=f"Departments not found for tenant {payload.tenant_code}: {', '.join(missing_depts)}"
            )

        # 5. Fetch existing defects
        existing_defects = db.query(models.Defect.defect_name).filter(
            models.Defect.tenant_id == requested_tenant.id
        ).all()
        existing_defect_names = {name[0].strip().lower() for name in existing_defects}

        # 6. Insert missing defects (vectorized)
        missing_defects_df = (
            df_input.loc[~df_input["defect_name"].isin(existing_defect_names), ["defect_name"]]
            .drop_duplicates()
            .assign(
                tenant_id=requested_tenant.id,
                created_by=current_user.id,
                updated_by=current_user.id
            )
        )

        if not missing_defects_df.empty:
            db.bulk_insert_mappings(
                models.Defect,
                missing_defects_df.to_dict(orient="records")
            )
            db.flush()  # ensure IDs are available

        # 7. Get all defect IDs
        all_defects = db.query(models.Defect).filter(
            models.Defect.tenant_id == requested_tenant.id
        ).all()
        defect_df = pd.DataFrame(
            [(d.defect_name.strip().lower(), d.id) for d in all_defects],
            columns=["defect_name", "defect_id"]
        )

        # 8. Merge defect IDs into input
        df_input = df_input.merge(defect_df, on="defect_name", how="left")
        df_input["tenant_id"] = requested_tenant.id
        df_input["created_by"] = current_user.id
        df_input["updated_by"] = current_user.id

        # 9. Remove already existing defect-department links
        existing_links = db.query(
            models.DefectDepartment.defect_id,
            models.DefectDepartment.department_id
        ).join(models.Defect).filter(
            models.Defect.tenant_id == requested_tenant.id
        ).all()

        existing_links_df = pd.DataFrame(existing_links, columns=["defect_id", "department_id"])

        if not existing_links_df.empty:
            df_input = df_input.merge(
                existing_links_df, 
                on=["defect_id", "department_id"], 
                how="left", 
                indicator=True
            )
            df_input = df_input[df_input["_merge"] == "left_only"].drop(columns=["_merge"])

        if df_input.empty:
            raise HTTPException(
                status_code=400,
                detail="All provided defect-department mappings already exist."
            )

        # 10. Insert new mappings
        db.bulk_insert_mappings(
            models.DefectDepartment,
            df_input[["tenant_id", "defect_id", "department_id", "created_by", "updated_by"]].to_dict(orient="records")
        )
        db.commit()

        # 11. Return inserted records
        return {
            "status": "success",
            "inserted": df_input[["defect_name", "department_id", "department_name"]].to_dict(orient="records")
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


#<------------------------Defect Departments Ends Here --------------------------


# -------------------------Down Time Departments Starts Here --------------------->

@router.post("/downTime-department", status_code=status.HTTP_201_CREATED)
def create_downtime_with_departments(
    payload: schemas.TenantDownTimeDepartment,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    try:
        # 1️⃣ Validate user & tenant
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)
        requested_tenant = backtable.getTenantByCode(payload.tenant_code, db)

        if payload.tenant_code != current_user.tenant.tenant_code:
            raise HTTPException(
                status_code=403,
                detail=f"User not authorised to create downtimes for {requested_tenant.tenant_name}"
            )

        # 2️⃣ Fetch tenant departments → DataFrame
        tenant_departments = db.query(models.Department).filter(
            models.Department.tenant_id == requested_tenant.id
        ).all()

        dept_df = pd.DataFrame(
            [(d.department_name.strip().lower(), d.id) for d in tenant_departments],
            columns=["department_name", "department_id"]
        )

        # 3️⃣ Convert payload to DataFrame
        try:
            payload_df = pd.DataFrame([d.dict() for d in payload.downtime])  # Pydantic v1
        except AttributeError:
            payload_df = pd.DataFrame([d.model_dump() for d in payload.downtime])  # Pydantic v2

        # Ensure department_names is always a list
        payload_df["department_names"] = payload_df["department_names"].apply(
            lambda x: [x] if isinstance(x, str) else x
        )

        # Explode departments & downtime names
        payload_df = payload_df.explode("department_names").explode("downtime_names")

        # Normalize names
        payload_df["department_name"] = payload_df["department_names"].str.strip().str.lower()
        payload_df["downtime_names"] = payload_df["downtime_names"].str.strip().str.lower()

        df_input = payload_df[["department_name", "downtime_names"]].drop_duplicates()

        # 4️⃣ Validate department names exist
        df_input = df_input.merge(dept_df, on="department_name", how="left")
        if df_input["department_id"].isnull().any():
            missing_depts = df_input.loc[df_input["department_id"].isnull(), "department_name"].unique()
            raise HTTPException(
                status_code=400,
                detail=f"Departments not found for tenant {payload.tenant_code}: {', '.join(missing_depts)}"
            )

        # 5️⃣ Fetch existing downtime names
        existing_downtime = db.query(models.DownTime.downtime_name).filter(
            models.DownTime.tenant_id == requested_tenant.id
        ).all()
        existing_downtime_names = {name[0].strip().lower() for name in existing_downtime}

        # 6️⃣ Insert missing downtime names
        missing_downtime_df = (
            df_input.loc[~df_input["downtime_names"].isin(existing_downtime_names), ["downtime_names"]]
            .drop_duplicates()
            .rename(columns={"downtime_names": "downtime_name"})  # ✅ match DB column
            .assign(
                tenant_id=requested_tenant.id,
                created_by=current_user.id,
                updated_by=current_user.id
            )
        )

        if not missing_downtime_df.empty:
            db.bulk_insert_mappings(
                models.DownTime,
                missing_downtime_df.to_dict(orient="records")
            )
            db.flush()  # get IDs for newly inserted rows

        # 7️⃣ Fetch all downtime IDs
        all_downtime = db.query(models.DownTime).filter(
            models.DownTime.tenant_id == requested_tenant.id
        ).all()
        downtime_df = pd.DataFrame(
            [(d.downtime_name.strip().lower(), d.id) for d in all_downtime],
            columns=["downtime_name", "downtime_id"]
        )

        # 8️⃣ Merge downtime IDs into df_input
        df_input = df_input.rename(columns={"downtime_names": "downtime_name"})
        df_input = df_input.merge(downtime_df, on="downtime_name", how="left")
        df_input["tenant_id"] = requested_tenant.id
        df_input["created_by"] = current_user.id
        df_input["updated_by"] = current_user.id

        # 9️⃣ Remove existing downtime-department mappings
        existing_links = db.query(
            models.DownTimeDepartment.downtime_id,
            models.DownTimeDepartment.department_id
        ).join(models.DownTime).filter(
            models.DownTime.tenant_id == requested_tenant.id
        ).all()

        existing_links_df = pd.DataFrame(existing_links, columns=["downtime_id", "department_id"])
        if not existing_links_df.empty:
            df_input = df_input.merge(
                existing_links_df,
                on=["downtime_id", "department_id"],
                how="left",
                indicator=True
            )
            df_input = df_input[df_input["_merge"] == "left_only"].drop(columns=["_merge"])

        if df_input.empty:
            raise HTTPException(
                status_code=400,
                detail="All provided downtime-department mappings already exist."
            )

        # 🔟 Insert new mappings
        db.bulk_insert_mappings(
            models.DownTimeDepartment,
            df_input[["tenant_id", "downtime_id", "department_id", "created_by", "updated_by"]].to_dict(orient="records")
        )
        db.commit()

        # 1️⃣1️⃣ Return inserted records
        return {
            "status": "success",
            "inserted": df_input[["downtime_name", "department_id", "department_name"]].to_dict(orient="records")
        }

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

#<------------------------Down Time Departments Ends Here --------------------------
