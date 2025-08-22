from fastapi import HTTPException, status
from sqlalchemy.orm import Session

# ✅ make sure this is defined outside any class

def get_entity(
    db: Session,
    model,
    current_user,
    field_name: str,
    field_value: str,
    entity_label: str
):
    tenant_id = current_user.tenant.id
    field = getattr(model, field_name)
    
    entity = db.query(model).filter(
        field == field_value,
        model.tenant_id == tenant_id
    ).first()

    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_label} '{field_value}' not found for Tenant {current_user.tenant.tenant_name}"
        )
    return entity
