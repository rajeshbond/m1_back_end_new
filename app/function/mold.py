from fastapi import HTTPException,status
from sqlalchemy.orm import Session
from .. import models, schemas


def get_product_and_mold(db: Session, tenant_id: int, product_name: str, mold_no: str):
    
    product = db.query(models.Product).filter(
        models.Product.product_name == product_name,
        models.Product.tenant_id == tenant_id
    ).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_name}' not found for current tenant"
        )

    mold = db.query(models.Mold).filter(
        models.Mold.mold_no == mold_no,
        models.Mold.tenant_id == tenant_id
    ).first()
    if not mold:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mold '{mold_no}' not found for current tenant"
        )

    return product, mold
