import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, insert, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError,SQLAlchemyError
from typing import List

from app.function.mold import get_product_and_mold
from .. import models, schemas, database, oauth2
from ..function import user,tenant,timeapp
from ..database import get_db
from datetime import date, time, datetime
from psycopg2.errors import UniqueViolation

router = APIRouter(
  prefix="/molds",
  tags=["Molds"]
)


@router.post("/mold", status_code=status.HTTP_201_CREATED, response_model=schemas.MoldCreateResponse)
def create_mold(mold: schemas.MoldCreate, db: Session = Depends(get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):
  
    try:
      # 1. Validate user, tenant, role
      user.get_user_status(current_user)
      tenant.user_role_admin(current_user)
      tenant_id = current_user.tenant.id
      exisiting_mold = db.query(models.Mold).filter(models.Mold.mold_no == mold.mold_no, models.Mold.tenant_id == tenant_id).first()
      if exisiting_mold:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Mold with name {mold.mold_no} already exists for {current_user.tenant.tenant_name}")
      new_mold = models.Mold(**mold.model_dump(),tenant_id=tenant_id,created_by=current_user.id,updated_by=current_user.id)
      db.add(new_mold)
      db.commit()
      db.refresh(new_mold)
      return {"message": "Mold created successfully", "mold": new_mold}
    except HTTPException as he:
      raise he
    except IntegrityError as e:
      db.rollback()
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Integrity error: {str(e.orig)}")
    except SQLAlchemyError as e:
      db.rollback()
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Database error: {str(e)}")
    except Exception as e:
      db.rollback()
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Internal server error{str(e)}")   
    
# Update the mold record 

@router.put("/mold", status_code=status.HTTP_200_OK, response_model=schemas.MoldCreateResponse)
def update_mold(
    payload: schemas.MoldUpdate,   # non-default first
    mold_id: int = Query(..., description="Mold ID to update"),  # default (Query param)
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(oauth2.get_current_user)
):
    try:
        # 1. Validate user, tenant, role
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)

        tenant_id = current_user.tenant.id
        existing_mold = db.query(models.Mold).filter(
            models.Mold.id == mold_id,
            models.Mold.tenant_id == tenant_id
        ).first()

        if not existing_mold:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mold with id {mold_id} not found for {current_user.tenant.tenant_name}"
            )

        existing_mold.mold_no = payload.mold_no
        existing_mold.updated_by = current_user.id
        
        db.add(existing_mold)

        db.commit()
        db.refresh(existing_mold)

        return {
            "message": "Mold updated successfully",
            "mold": existing_mold
        }

    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Integrity error: {str(e.orig)}"
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/mold", status_code=status.HTTP_204_NO_CONTENT)
def delete_mold(
    mold_id: int = Query(..., description="Mold ID to delete"),
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(oauth2.get_current_user)
):
    try:
        # 1. Validate user, tenant, role
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)

        tenant_id = current_user.tenant.id  
        existing_mold = db.query(models.Mold).filter(
            models.Mold.id == mold_id,
            models.Mold.tenant_id == tenant_id
        ).first()

        if not existing_mold:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mold with id {mold_id} not found for {current_user.tenant.tenant_name}"
            )

        db.delete(existing_mold)
        db.commit()

        return {
            "message": "Mold deleted successfully"
        }

    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Integrity error: {str(e.orig)}"
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
    

# ----Product mold mapping----

from fastapi import HTTPException

@router.post("/product-mold", status_code=status.HTTP_200_OK)
def create_product_mold(
    product_mold: schemas.ProductMoldCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(oauth2.get_current_user),
):
    try:
        # --- Validation ---
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)
        tenant_id = current_user.tenant.id  

        # --- Find product ---
        product = db.query(models.Product).filter(
            models.Product.product_name == product_mold.product_name,
            models.Product.tenant_id == tenant_id
        ).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{product_mold.product_name}' not found for current tenant"
            )

        # --- Find mold ---
        mold = db.query(models.Mold).filter(
            models.Mold.mold_no == product_mold.mold_no,
            models.Mold.tenant_id == tenant_id
        ).first()
        if not mold:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mold '{product_mold.mold_no}' not found for current tenant"
            )

        # --- Check mapping ---
        existing_pm = db.query(models.ProductMold).filter(
            models.ProductMold.product_id == product.id,
            models.ProductMold.mold_id == mold.id
        ).first()
        if existing_pm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This Product-Mold mapping already exists"
            )

        # --- Create mapping ---
        new_pm = models.ProductMold(
            product_id=product.id,
            mold_id=mold.id,
            created_by=current_user.id,
            updated_by=current_user.id,
        )
        db.add(new_pm)
        db.commit()
        db.refresh(new_pm)

        return {
            "message": "Product-Mold created successfully",
            "data": {
                "id": new_pm.id,
                "product_name": product.product_name,
                "mold_no": mold.mold_no
            }
        }

    except HTTPException:  # ✅ Let FastAPI handle intentional errors
        raise
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Integrity error: {str(e.orig)}"
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.put("/{pm_id}", response_model=schemas.ProductMoldOut)
def update_product_mold(
    pm_id: int,
    payload: schemas.ProductMoldUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(oauth2.get_current_user)
):
    try:
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)
        tenant_id = current_user.tenant.id

        pm = db.query(models.ProductMold).filter(
            models.ProductMold.id == pm_id,
            models.ProductMold.tenant_id == tenant_id
        ).first()
        if not pm:
            raise HTTPException(status_code=404, detail="Product-Mold mapping not found")

        product, mold = get_product_and_mold(db, tenant_id, payload.product_name, payload.mold_no)

        # Check duplicate mapping (avoid updating into an existing pair)
        duplicate = db.query(models.ProductMold).filter(
            models.ProductMold.product_id == product.id,
            models.ProductMold.mold_id == mold.id,
            models.ProductMold.tenant_id == tenant_id,
            models.ProductMold.id != pm_id
        ).first()
        if duplicate:
            raise HTTPException(
                status_code=400,
                detail="This Product-Mold mapping already exists"
            )

        pm.product_id = product.id
        pm.mold_id = mold.id
        pm.updated_by = current_user.id

        db.commit()
        db.refresh(pm)

        return schemas.ProductMoldOut(
            id=pm.id,
            product_name=product.product_name,
            mold_no=mold.mold_no,
            created_at=pm.created_at,
            updated_at=pm.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    

# 🔹 READ (all for tenant)
@router.get("/", response_model=list[schemas.ProductMoldOut])
def list_product_molds(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(oauth2.get_current_user)
):
    tenant_id = current_user.tenant.id
    mappings = (
        db.query(models.ProductMold, models.Product, models.Mold)
        .join(models.Product, models.ProductMold.product_id == models.Product.id)
        .join(models.Mold, models.ProductMold.mold_id == models.Mold.id)
        .filter(models.Product.tenant_id == tenant_id)   # ✅ filter via Product
        .filter(models.Mold.tenant_id == tenant_id)      # ✅ filter via Mold
        .all()
    )

    return [
        schemas.ProductMoldOut(
            id=pm.ProductMold.id,
            product_name=pm.Product.product_name,
            mold_no=pm.Mold.mold_no,
            created_at=pm.ProductMold.created_at,
            updated_at=pm.ProductMold.updated_at,
        )
        for pm in mappings
    ]

@router.get("/{pm_id}", response_model=schemas.ProductMoldOut)
def get_product_mold(
    pm_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(oauth2.get_current_user)
):
    tenant_id = current_user.tenant.id

    pm = (
        db.query(models.ProductMold, models.Product, models.Mold)
        .join(models.Product, models.ProductMold.product_id == models.Product.id)
        .join(models.Mold, models.ProductMold.mold_id == models.Mold.id)
        .filter(models.ProductMold.id == pm_id)
        .filter(models.Product.tenant_id == tenant_id)  # ✅ tenant check for product
        .filter(models.Mold.tenant_id == tenant_id)     # ✅ tenant check for mold
        .first()
    )

    if not pm:
        raise HTTPException(
            status_code=404,
            detail=f"Product-Mold mapping with id {pm_id} not found for current tenant"
        )

    return schemas.ProductMoldOut(
        id=pm.ProductMold.id,
        product_name=pm.Product.product_name,
        mold_no=pm.Mold.mold_no,
        created_at=pm.ProductMold.created_at,
        updated_at=pm.ProductMold.updated_at,
    )




