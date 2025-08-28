import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, insert, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError,SQLAlchemyError
from typing import List

from app.function.mold import get_product_and_mold
from .. import models, schemas, database, oauth2
from ..function import mold_mach, user,tenant,timeapp,mold_mach
from ..database import get_db
from datetime import date, time, datetime
from psycopg2.errors import UniqueViolation

router = APIRouter(prefix="/mold-machines", tags=["MoldMachine"])



@router.post("/", status_code=status.HTTP_201_CREATED)
def create_mold_machine(
    mold_machine: schemas.MoldMachineCreate,
    db: Session = Depends(database.get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    try:
        # validate user, tenant, role
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)
        tenant_id = current_user.tenant.id

        mold = mold_mach.get_entity(db, models.Mold, current_user, "mold_no", mold_machine.mold_no, "Mold")

        # 🔹 Find the machine using generic fetcher
        machine = mold_mach.get_entity(db, models.Machine, current_user, "machine_code", mold_machine.machine_code, "Machine")

        # 🔹 check for mapping
        mapping = db.query(models.MoldMachine).filter(
            models.MoldMachine.mold_id == mold.id,
            models.MoldMachine.machine_id == machine.id,
            models.MoldMachine.tenant_id == tenant_id
        ).first()
        if mapping:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Mold Machine mapping already exists for Tenant {current_user.tenant.tenant_name}"
            )

        # 🔹 Create the mold machine mapping
        new_mold_machine = models.MoldMachine(
            mold_id=mold.id,
            machine_id=machine.id,
            tenant_id=tenant_id,
            created_by=current_user.id,
            updated_by=current_user.id
        )
        db.add(new_mold_machine)
        db.commit()
        db.refresh(new_mold_machine)

        return {
            "message": "Mold Machine created successfully",
            "mold_machine": new_mold_machine
        }

    except HTTPException as he:
        raise he
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")
    except IntegrityError as e:
        raise HTTPException(status_code=500, detail=f"Integrity Error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.put("/{mold_machine_id}",status_code=status.HTTP_200_OK,response_model=schemas.MoldMachineOut)
def update_mold_machine(
  mold_machine_id: int,
  update_data: schemas.MoldMachineUpdate,
  db: Session = Depends(database.get_db),
  current_user: int = Depends(oauth2.get_current_user)
):
  # validate user
  user.get_user_status(current_user)
  tenant.user_role_admin(current_user)
  
  mapping = db.query(models.MoldMachine).filter(
        models.MoldMachine.id == mold_machine_id,
        models.MoldMachine.tenant_id == current_user.tenant_id
    ).first()

  if not mapping:
        raise HTTPException(status_code=404, detail="Mold Machine mapping not found")

    # If updating mold
  if update_data.mold_no:
        mold = mold_mach.get_entity(db, models.Mold, current_user, "mold_no", update_data.mold_no, "Mold")
        mapping.mold_id = mold.id

    # If updating machine
  if update_data.machine_code:
        machine = mold_mach.get_entity(db, models.Machine, current_user, "machine_code", update_data.machine_code, "Machine")
        mapping.machine_id = machine.id

  mapping.updated_by = current_user.id
  db.commit()
  db.refresh(mapping)
  return mapping


# Delete
@router.delete("/{mold_machine_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_mold_machine(
  mold_machine_id: int,
  db: Session = Depends(database.get_db),
  current_user: int = Depends(oauth2.get_current_user)
):
  

  
  # Validation
  user.get_user_status(current_user)
  tenant.user_role_admin(current_user)
  tenant_id = current_user.tenant_id
  mapping = db.query(models.MoldMachine).join(models.Mold,models.Mold.id == models.MoldMachine.mold_id).join(models.Machine,models.Machine.id == models.MoldMachine.machine_id).filter(models.MoldMachine.id == mold_machine_id,models.Mold.tenant_id==tenant_id,models.Machine.tenant_id == tenant_id).first()

  if not mapping:
    raise HTTPException(status_code=404, detail=f"Mold Machine mapping not found for tenant {current_user.tenant.tenant_name}")

  db.delete(mapping)
  db.commit()
  return {"message": "Mold Machine mapping deleted successfully"}

@router.get("/",status_code=status.HTTP_200_OK,response_model=List[schemas.MoldMachineOut])
def get_mold_machines(db: Session = Depends(database.get_db),
    current_user: int = Depends(oauth2.get_current_user)):
  # validate
  user.get_user_status(current_user)
  tenant_id = current_user.tenant_id
  mappings = db.query(models.MoldMachine).join(models.Mold,models.Mold.id == models.MoldMachine.mold_id).join(models.Machine,models.Machine.id == models.MoldMachine.machine_id).filter(models.Mold.tenant_id == tenant_id,models.Machine.tenant_id==tenant_id).all()
  if not mappings:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Not Mold Machine mapping found for Tenant {current_user.tenant.tenant_name}")
  return mappings

# Read 

@router.get("/{mold_machine_id}",response_model=schemas.MoldMachineOut,status_code=status.HTTP_200_OK)
def get_mold_machine(
  mold_machine_id: int,
  db: Session = Depends(database.get_db),
  current_user: int = Depends(oauth2.get_current_user)
    
):
  # Validate 
  user.get_user_status(current_user)
  tenant_id = current_user.tenant_id

  mapping = db.query(models.MoldMachine).join(models.Mold,models.Mold.id == models.MoldMachine.mold_id).join(models.Machine,models.Machine.id == models.MoldMachine.machine_id).filter(models.MoldMachine.id == mold_machine_id,models.Mold.tenant_id==tenant_id,models.Machine.tenant_id == tenant_id).first()
  if not mapping:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Not Mold Machine mapping found for Tenant {current_user.tenant.tenant_name}")
  return mapping

