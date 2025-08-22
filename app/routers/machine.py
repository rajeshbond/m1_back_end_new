import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, insert, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError,SQLAlchemyError
from typing import List
from .. import models, schemas, database, oauth2
from ..function import user,tenant,timeapp
from ..database import get_db
from datetime import date, time, datetime
from psycopg2.errors import UniqueViolation

router = APIRouter(prefix="/machine", tags=["Machine"])


# ---------------- CREATE ----------------
@router.post("/add", status_code=status.HTTP_201_CREATED)
def create_machine(
    machine: schemas.MachineCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(oauth2.get_current_user)
):
    try:
        # 1. Validate user, tenant, role
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)
        tenant_id = current_user.tenant.id

        # 2. Duplicate check
        existing_machine = db.query(models.Machine).filter(
            models.Machine.machine_code == machine.machine_code,
            models.Machine.tenant_id == tenant_id
        ).first()
        if existing_machine:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Machine with code {machine.machine_code} already exists for tenant {current_user.tenant.tenant_name}"
            )

        # 3. Create new machine
        new_machine = models.Machine(
            **machine.model_dump(),
            tenant_id=tenant_id,
            created_by=current_user.id,
            updated_by=current_user.id
        )
        db.add(new_machine)
        db.commit()
        db.refresh(new_machine)

        return {"message": "Machine created successfully", "machine": schemas.MachineOut.model_validate(new_machine)}

    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Integrity error: {str(e.orig)}")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ---------------- UPDATE (PUT) ----------------
@router.put("/editmachine", status_code=status.HTTP_200_OK)
def update_machine(
    payload: schemas.MachineUpdate,
    machine_id: int = Query(..., description="Machine ID to update"),
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(oauth2.get_current_user)
):
    try:
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)
        tenant_id = current_user.tenant.id

        payload_exist_machine = db.query(models.Machine).filter(models.Machine.machine_code == payload.machine_code, models.Machine.tenant_id == tenant_id).first()

        if payload_exist_machine and payload_exist_machine.id != machine_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Machine with code {payload.machine_code} already exists for tenant {current_user.tenant.tenant_name}"
            )
        existing_machine = db.query(models.Machine).filter(
            models.Machine.id == machine_id,
            models.Machine.tenant_id == tenant_id
        ).first()

        if not existing_machine:
            raise HTTPException(
                status_code=404,
                detail=f"Machine with id {machine_id} not found for {current_user.tenant.tenant_name}"
            )

        # Update fields only if provided
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(existing_machine, key, value)

        existing_machine.updated_by = current_user.id

        db.add(existing_machine)
        db.commit()
        db.refresh(existing_machine)

        return {"message": "Machine updated successfully", "updated machine": schemas.MachineOut.model_validate(existing_machine)}

    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Integrity error: {str(e.orig)}")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ---------------- PATCH (Partial Update) ----------------
@router.patch("/", status_code=status.HTTP_200_OK, response_model=schemas.MachineOut)
def patch_machine(
    payload: schemas.MachineUpdate,
    machine_id: int = Query(..., description="Machine ID to patch"),
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(oauth2.get_current_user)
):
    return update_machine(payload, machine_id, db, current_user)


# ---------------- DELETE ----------------
@router.delete("/delete", status_code=status.HTTP_200_OK)
def delete_machine(
    machine_id: int = Query(..., description="Machine ID to delete"),
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(oauth2.get_current_user)
):
    print(machine_id)
    try:
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)
        tenant_id = current_user.tenant.id

        machine = db.query(models.Machine).filter(
            models.Machine.id == machine_id,
            models.Machine.tenant_id == tenant_id
        ).first()

        if not machine:
            raise HTTPException(
                status_code=404,
                detail=f"Machine with id {machine_id} not found for {current_user.tenant.tenant_name}"
            )

        db.delete(machine)
        db.commit()

        return {"message": "Machine deleted successfully"}

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
