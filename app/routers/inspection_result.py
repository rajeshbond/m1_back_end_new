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
router = APIRouter(prefix="/inspection-results", tags=["Inspection Results"])

# def is_time_in_shift_range(inspect_time: time, shift_start: time, shift_end: time) -> bool:
#     """Check if inspect_time is within shift time range (handles overnight shifts)."""
#     if shift_start <= shift_end:
#         # Normal shift within same day, e.g., 09:00 to 17:00
#         return shift_start <= inspect_time <= shift_end
#     else:
#         # Overnight shift, e.g., 23:00 to 06:00 next day
#         return inspect_time >= shift_start or inspect_time <= shift_end

@router.post("/record", response_model=schemas.ProductInspectionResultResponse)
def create_inspection_result(
    payload: schemas.ProductInspectionResultCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):

    tenant_id = current_user.tenant_id

    # 1️⃣ Validate Inspector Exists
    inspector = db.query(models.User).filter(
        models.User.id == payload.inspector_id,
        models.User.tenant_id == tenant_id
    ).first()
    if not inspector:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Inspector ID {payload.inspector_id} does not exist for this tenant."
        )

    # 2️⃣ Validate ShiftTiming via TenantShift -> Tenant
    shift_timing = db.query(models.ShiftTiming).join(models.TenantShift).filter(
        models.ShiftTiming.id == payload.shift_timingid,
        models.TenantShift.tenant_id == tenant_id
    ).first()
    if not shift_timing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid shift_timingid for this tenant."
        )

    # 3️⃣ Validate inspection hour is within shift time (handle overnight shifts)
    inspection_hour = payload.inspection_hour
    inspection_time_obj = time(inspection_hour, 0)

    if not timeapp.is_time_in_shift_range(inspection_time_obj, shift_timing.shift_start, shift_timing.shift_end):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Inspection hour {inspection_hour:02d}:00 is outside shift time range "
                   f"{shift_timing.shift_start.strftime('%H:%M')} - {shift_timing.shift_end.strftime('%H:%M')}."
        )

    # 4️⃣ Ensure max 8 inspections per shift
    count_existing = db.query(models.ProductInspectionResult).filter(
        models.ProductInspectionResult.shift_timingid == payload.shift_timingid,
        models.ProductInspectionResult.inspection_date == payload.inspection_date
    ).count()
    if count_existing >= 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum inspection count (8) reached for this shift."
        )

    # 5️⃣ Check for duplicate inspection for same inspection_id, date, and hour
    duplicate = db.query(models.ProductInspectionResult).filter(
        models.ProductInspectionResult.inspection_id == payload.inspection_id,
        models.ProductInspectionResult.inspection_date == payload.inspection_date,
        models.ProductInspectionResult.inspection_hour == payload.inspection_hour
    ).first()
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate inspection result detected."
        )

    # 6️⃣ Create inspection result
    new_result = models.ProductInspectionResult(
        **payload.model_dump(),
        created_by=current_user.id,
        updated_by=current_user.id
    )

    db.add(new_result)
    try:
        db.commit()
        db.refresh(new_result)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database error: {str(e)}"
        )

    return new_result

# @router.post("/record", response_model=schemas.ProductInspectionResultResponse)
# def create_inspection_result(
#     payload: schemas.ProductInspectionResultCreate,
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(oauth2.get_current_user)
# ):

#         # 1️⃣ Validate user
#     tenant_id = current_user.tenant_id


#     # 1️⃣ Validate Inspector Exists
#     inspector = db.query(models.User).filter(
#         models.User.id == payload.inspector_id,
#         models.User.tenant_id == tenant_id
#     ).first()
#     if not inspector:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Inspector ID {payload.inspector_id} does not exist for this tenant."
#         )

#     # 2️⃣ Validate ShiftTiming via TenantShift -> Tenant
#     shift_timing = db.query(models.ShiftTiming).join(models.TenantShift).filter(
#         models.ShiftTiming.id == payload.shift_timingid,
#         models.TenantShift.tenant_id == tenant_id
#     ).first()
#     if not shift_timing:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Invalid shift_timingid for this tenant."
#         )

#     # 3️⃣ Validate inspection hour is within shift time
#     inspection_hour = payload.inspection_hour
#     inspection_time_obj = time(inspection_hour, 0)
#     if not (shift_timing.shift_start <= inspection_time_obj <= shift_timing.shift_end):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Inspection hour {inspection_hour:02d}:00 is outside shift time range "
#                    f"{shift_timing.shift_start.strftime('%H:%M')} - {shift_timing.shift_end.strftime('%H:%M')}."
#         )

#     # 4️⃣ Ensure max 8 inspections per shift
#     count_existing = db.query(models.ProductInspectionResult).filter(
#         models.ProductInspectionResult.shift_timingid == payload.shift_timingid,
#         models.ProductInspectionResult.inspection_date == payload.inspection_date
#     ).count()
#     if count_existing >= 8:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Maximum inspection count (8) reached for this shift."
#         )

#     # 5️⃣ Check for duplicate inspection for same inspection_id, date, and hour
#     duplicate = db.query(models.ProductInspectionResult).filter(
#         models.ProductInspectionResult.inspection_id == payload.inspection_id,
#         models.ProductInspectionResult.inspection_date == payload.inspection_date,
#         models.ProductInspectionResult.inspection_hour == payload.inspection_hour
#     ).first()
#     if duplicate:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Duplicate inspection result detected."
#         )

#     # 6️⃣ Create inspection result
#     new_result = models.ProductInspectionResult(
#         **payload.model_dump(),
#         created_by=current_user.id,
#         updated_by=current_user.id
#     )

#     db.add(new_result)
#     try:
#         db.commit()
#         db.refresh(new_result)
#     except IntegrityError as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Database integrity error: {str(e.orig)}"
#         )

#     return new_result

# @router.post("/record", response_model=schemas.ProductInspectionResultResponse)
# def create_inspection_result(
#     payload: schemas.ProductInspectionResultCreate,
#     db: Session = Depends(get_db),
#     current_user: int = Depends(oauth2.get_current_user)
# ):
#     try:
#         # 1️⃣ Validate user
#         user.get_user_status(current_user)
#         tenant_id = current_user.tenant.id

#         # 2️⃣ Ensure inspection belongs to tenant via product → drawing → inspection
#         inspection = (
#             db.query(models.ProductInspection)
#             .join(models.ProductDrawing, models.ProductInspection.drawing_id == models.ProductDrawing.id)
#             .join(models.Product, models.ProductDrawing.product_id == models.Product.id)
#             .filter(models.ProductInspection.id == payload.inspection_id)
#             .filter(models.Product.tenant_id == tenant_id)
#             .first()
#         )
#         if not inspection:
#             raise HTTPException(status_code=404, detail="Inspection not found for your tenant.")

#         # 3️⃣ Ensure shift timing belongs to tenant via TenantShift
#         shift_timing = (
#             db.query(models.ShiftTiming)
#             .join(models.TenantShift, models.ShiftTiming.tenant_shift_id == models.TenantShift.id)
#             .filter(models.ShiftTiming.id == payload.shift_timingid)
#             .filter(models.TenantShift.tenant_id == tenant_id)
#             .first()
#         )
#         if not shift_timing:
#             raise HTTPException(status_code=404, detail="Shift timing not found for your tenant.")

#         # 4️⃣ Check inspection hour within shift range
#         inspection_time = time(payload.inspection_hour, 0)
#         if not (shift_timing.shift_start <= inspection_time <= shift_timing.shift_end):
#             raise HTTPException(
#                 status_code=400,
#                 detail=(
#                     f"Inspection hour {payload.inspection_hour:02d}:00 is outside "
#                     f"shift time range {shift_timing.shift_start.strftime('%H:%M')} - {shift_timing.shift_end.strftime('%H:%M')}."
#                 )
#             )

#         # 5️⃣ Calculate allowed inspections based on shift duration
#         shift_duration_hours = (
#             datetime.combine(date.today(), shift_timing.shift_end)
#             - datetime.combine(date.today(), shift_timing.shift_start)
#         ).seconds // 3600
#         shift_duration_hours = max(shift_duration_hours, 1)  # avoid divide-by-zero

#         # 6️⃣ Count existing for shift/date/tenant
#         count_existing = (
#             db.query(models.ProductInspectionResult)
#             .join(models.ProductInspection, models.ProductInspectionResult.inspection_id == models.ProductInspection.id)
#             .join(models.ProductDrawing, models.ProductInspection.drawing_id == models.ProductDrawing.id)
#             .join(models.Product, models.ProductDrawing.product_id == models.Product.id)
#             .filter(models.Product.tenant_id == tenant_id)
#             .filter(models.ProductInspectionResult.shift_timingid == payload.shift_timingid)
#             .filter(models.ProductInspectionResult.inspection_date == payload.inspection_date)
#             .count()
#         )
#         if count_existing >= shift_duration_hours:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Maximum of {shift_duration_hours} inspection results allowed for this shift and date."
#             )

#         # 7️⃣ Duplicate check for exact shift/date/hour
#         duplicate_exists = (
#             db.query(models.ProductInspectionResult)
#             .join(models.ProductInspection, models.ProductInspectionResult.inspection_id == models.ProductInspection.id)
#             .join(models.ProductDrawing, models.ProductInspection.drawing_id == models.ProductDrawing.id)
#             .join(models.Product, models.ProductDrawing.product_id == models.Product.id)
#             .filter(models.Product.tenant_id == tenant_id)
#             .filter(models.ProductInspectionResult.shift_timingid == payload.shift_timingid)
#             .filter(models.ProductInspectionResult.inspection_date == payload.inspection_date)
#             .filter(models.ProductInspectionResult.inspection_hour == payload.inspection_hour)
#             .first()
#         )
#         if duplicate_exists:
#             raise HTTPException(status_code=400, detail="Inspection result already exists for this shift/date/hour.")

#         # 8️⃣ Create and save record
#         new_result = models.ProductInspectionResult(
#             **payload.model_dump(),
#             created_by=current_user.id,
#             updated_by=current_user.id
#         )
#         db.add(new_result)
#         db.commit()
#         db.refresh(new_result)
#         return new_result

#     except IntegrityError as e:
#         db.rollback()
#         if isinstance(e.orig, UniqueViolation):
#             raise HTTPException(status_code=400, detail="Duplicate inspection result detected.")
#         else:
#             raise HTTPException(status_code=400, detail=f"Database integrity error: {str(e.orig)}")

#     except HTTPException:
#         raise

#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


#  update 

@router.put("/update", response_model=schemas.ProductInspectionResultResponse)
def update_result(
    result_id: int,
    payload: schemas.ProductInspectionResultUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    result = db.query(models.ProductInspectionResult).filter(models.ProductInspectionResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found")

    # Validate inspection_hour if provided
    update_data = payload.model_dump(exclude_unset=True)
    inspection_hour = update_data.get("inspection_hour", result.inspection_hour)
    shift_timing = db.query(models.ShiftTiming).filter(models.ShiftTiming.id == result.shift_timingid).first()

    if shift_timing:
        inspection_time_obj = time(inspection_hour, 0)
        if not timeapp.is_time_in_shift_range(inspection_time_obj, shift_timing.shift_start, shift_timing.shift_end):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Inspection hour {inspection_hour:02d}:00 is outside shift time range "
                    f"{shift_timing.shift_start.strftime('%H:%M')} - {shift_timing.shift_end.strftime('%H:%M')}."
                )
            )

    # Update fields
    for key, value in update_data.items():
        setattr(result, key, value)
    result.updated_by = current_user.id

    # Check for duplicates if inspection_id, inspection_date, inspection_hour or shift_timingid changed
    # Prepare filters excluding current record id
    inspection_id = update_data.get("inspection_id", result.inspection_id)
    inspection_date = update_data.get("inspection_date", result.inspection_date)
    shift_timingid = update_data.get("shift_timingid", result.shift_timingid)

    duplicate = db.query(models.ProductInspectionResult).filter(
        models.ProductInspectionResult.inspection_id == inspection_id,
        models.ProductInspectionResult.inspection_date == inspection_date,
        models.ProductInspectionResult.inspection_hour == inspection_hour,
        models.ProductInspectionResult.shift_timingid == shift_timingid,
        models.ProductInspectionResult.id != result_id
    ).first()

    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate entry for this shift, date, and hour."
        )

    try:
        db.commit()
        db.refresh(result)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {str(e.orig)}"
        )

    return result


# Read All Records

@router.get("/", response_model=List[schemas.ProductInspectionResultResponse])
def get_all_results(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    user.get_user_status(current_user)
    tenant_id = current_user.tenant_id
    all_records = db.query(models.ProductInspectionResult).join(models.ProductInspection).join(models.ProductDrawing).join(models.Product).filter(models.Product.tenant_id == tenant_id).offset(skip).limit(limit).all()
    # all_records = db.query(models.ProductInspectionResult).filter(models.ProductInspectionResult.inspection.drawing.product.tenant_id == tenant_id).all()
    # return db.query(models.ProductInspectionResult).offset(skip).limit(limit).all()
    return all_records

# get record by id

@router.get("/{result_id}", response_model=schemas.ProductInspectionResultResponse)  
def get_result(result_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    user.get_user_status(current_user)
    tenant_id = current_user.tenant_id
    record = db.query(models.ProductInspectionResult).join(models.ProductInspection).join(models.ProductDrawing).join(models.Product).filter(models.Product.tenant_id == tenant_id).filter(models.ProductInspectionResult.id == result_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Result not found with id: {result_id} not belonging to this tenant {tenant_id}")
    return record

# delete record by id

@router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_result(result_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    user.get_user_status(current_user)
    tenant_id = current_user.tenant_id
    record = db.query(models.ProductInspectionResult).join(models.ProductInspection).join(models.ProductDrawing).join(models.Product).filter(models.Product.tenant_id == tenant_id).filter(models.ProductInspectionResult.id == result_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Result not found with id: {result_id} not belonging to this tenant {tenant_id}")
    db.delete(record)
    db.commit()
    return  