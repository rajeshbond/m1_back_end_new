import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import insert, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError,SQLAlchemyError
from typing import List
from .. import models, schemas, database, oauth2
from ..function import user,tenant
from ..database import get_db
router = APIRouter(
    prefix="/product-inspections",
    tags=["Product Inspection"]
)
def update_model_from_dict(model_obj, update_dict):
    for key, value in update_dict.items():
        setattr(model_obj, key, value)
# inspection entry -------------------------------------

@router.post("/bulk", response_model=list[schemas.ProductInspectionResponse])
def create_product_inspections_bulk(
    request: schemas.ProductInspectionBulkCreate,
    db: Session = Depends(database.get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    try:
        # Step 1: Validate user & tenant
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)
        tenant_id = current_user.tenant.id  # Tenant scope

        if not request.inspections:
            raise HTTPException(status_code=400, detail="No inspection data provided.")

        # Step 1.5: Validate that drawing belongs to tenant
        drawing = (
            db.query(models.ProductDrawing)
            .join(models.Product, models.Product.id == models.ProductDrawing.product_id)
            .filter(
                models.ProductDrawing.id == request.drawing_id,
                models.Product.tenant_id == tenant_id
            )
            .first()
        )
        if not drawing:
            raise HTTPException(
                status_code=404,
                detail=f"Drawing {request.drawing_id} not found for your tenant {current_user.tenant.tenant_name}."
            )

        # Step 2: Convert inspections to DataFrame
        df = pd.DataFrame([i.model_dump() for i in request.inspections], dtype="object")

        # Normalize dimension names for comparison
        df["dimension_name"] = df["dimension_name"].str.strip().str.lower()

        # Step 3: Check for duplicates inside request
        if df.duplicated(subset=["dimension_name"]).any():
            raise HTTPException(status_code=400, detail="Duplicate dimension names in request.")

        # Step 4: Check for duplicates already in DB for this drawing
        existing_records = db.execute(
            select(models.ProductInspection.dimension_name)
            .where(models.ProductInspection.drawing_id == request.drawing_id)
        ).all()

        existing_df = pd.DataFrame(existing_records, columns=["dimension_name"])
        existing_df["dimension_name"] = existing_df["dimension_name"].str.strip().str.lower()

        # Step 5: Remove already existing dimensions from DataFrame
        if not existing_df.empty:
            df = df[~df["dimension_name"].isin(existing_df["dimension_name"])]

        if df.empty:
            raise HTTPException(
                status_code=400,
                detail="All provided dimensions already exist for this drawing."
            )

        # Step 6: Add required columns
        df["drawing_id"] = request.drawing_id
        df["created_by"] = current_user.id
        df["updated_by"] = current_user.id

        # Step 7: Bulk insert using RETURNING (PostgreSQL)
        insert_stmt = (
            insert(models.ProductInspection)
            .values(df.to_dict(orient="records"))
            .returning(models.ProductInspection)
        )
        inserted_rows = db.execute(insert_stmt).fetchall()
        db.commit()

        # Step 8: Return inserted rows as ORM objects
        return [row[0] for row in inserted_rows]

    except IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Integrity error: {str(e.orig)}")
    except HTTPException as he:
        raise he
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"SQLAlchemy error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# @router.post("/bulk", response_model=list[schemas.ProductInspectionResponse])
# def create_product_inspections_bulk(
#     request: schemas.ProductInspectionBulkCreate,
#     db: Session = Depends(database.get_db),
#     current_user: int = Depends(oauth2.get_current_user)
# ):
#     try:
#         # Step 1: Validate user & tenant
#         user.get_user_status(current_user)
#         tenant.user_role_admin(current_user)
#         tenant_id = current_user.tenant.id  # For potential tenant scoping if needed

#         if not request.inspections:
#             raise HTTPException(status_code=400, detail="No inspection data provided.")

#         # Step 2: Convert inspections to DataFrame
#         df = pd.DataFrame([i.model_dump() for i in request.inspections], dtype="object")

#         # Normalize dimension names for comparison
#         df["dimension_name"] = df["dimension_name"].str.strip().str.lower()

#         # Step 3: Check for duplicates inside request
#         if df.duplicated(subset=["dimension_name"]).any():
#             raise HTTPException(status_code=400, detail="Duplicate dimension names in request.")

#         # Step 4: Check for duplicates already in DB for this drawing
#         existing_records = db.execute(
#             select(models.ProductInspection.dimension_name)
#             .where(models.ProductInspection.drawing_id == request.drawing_id)
#         ).all()

#         existing_df = pd.DataFrame(existing_records, columns=["dimension_name"])
#         existing_df["dimension_name"] = existing_df["dimension_name"].str.strip().str.lower()

#         # Step 5: Remove already existing dimensions from DataFrame
#         if not existing_df.empty:
#             df = df[~df["dimension_name"].isin(existing_df["dimension_name"])]

#         if df.empty:
#             raise HTTPException(status_code=400, detail="All provided dimensions already exist for this drawing.")

#         # Step 6: Add required columns
#         df["drawing_id"] = request.drawing_id
#         df["created_by"] = current_user.id
#         df["updated_by"] = current_user.id


#         # Step 7: Bulk insert using RETURNING (PostgreSQL)
#         insert_stmt = (
#             insert(models.ProductInspection)
#             .values(df.to_dict(orient="records"))
#             .returning(models.ProductInspection)
#         )
#         inserted_rows = db.execute(insert_stmt).fetchall()
#         db.commit()

#         # Step 8: Return inserted rows as ORM objects
#         return [row[0] for row in inserted_rows]

#     except IntegrityError as e:
#         raise HTTPException(status_code=400, detail=f"Integrity error: {str(e.orig)}")
#     except HTTPException as he:
#         raise he
#     except SQLAlchemyError as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"SQLAlchemy error: {str(e)}")
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    

# ---- update the inspection 

@router.put("/{inspection_id}", response_model=schemas.ProductInspectionResponse)
def update_product_inspection(
    inspection_id: int,
    request: schemas.ProductInspectionUpdate,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    try:
        # Step 1: Validate user and tenant role
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)
        tenant_id = current_user.tenant.id

        # Step 2: Fetch the inspection record
        inspection = db.query(models.ProductInspection).filter(models.ProductInspection.id == inspection_id).first()
        if not inspection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data found for inspection ID {inspection_id}"
            )

        # Step 3: Tenant ownership check (adjust attribute names as per your models)
        if inspection.product_drawings.products.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Inspection ID {inspection_id} does not belong to your tenant."
            )

        # Step 4: Update fields using helper function
        update_data = request.model_dump(exclude_unset=True)
        update_model_from_dict(inspection, update_data)

        inspection.updated_by = current_user.id

        # Step 5: Commit and refresh
        db.commit()
        db.refresh(inspection)

        return inspection

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Integrity error: {str(e.orig)}")
    except HTTPException as he:
        raise he
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"SQLAlchemy error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
# Delete the inpsection Drawing
@router.delete("/delete", response_model=dict)
def delete_product_inspection(
    inspection_id: int = Query(..., description="ID of the inspection to delete"),
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)):
    try:
        # validate user and tenant
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)
        tenant_id = current_user.tenant.id

        inspection = (
            db.query(models.ProductInspection).join(models.ProductDrawing).join(models.Product).join(models.Tenant).filter(models.ProductInspection.id == inspection_id, models.Tenant.id == tenant_id).first()
        )
        if not inspection:
            raise HTTPException(status_code=404, detail="Inspection not found or access denied")
        db.delete(inspection)
        db.commit()
        return{"deleted_id":inspection_id}

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Integrity error: {str(e.orig)}")
    except HTTPException as he:
        raise he
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"SQLAlchemy error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")