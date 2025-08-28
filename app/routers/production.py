from datetime import date, datetime
from operator import and_
from typing import List
from fastapi import Response, status,HTTPException,Depends,APIRouter
import pandas as pd
from sqlalchemy import tuple_
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from ..function import tenant,user

from .. import schemas,oauth2,models
# from ..function import ad
from .. import utls
from ..database import get_db


router = APIRouter(
    prefix="/production/v1",
    tags=["Production_Log"]
)

@router.post("/production-log/")
def create_production_log(
    payload: schemas.ProductionLogCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    # -------------------
    # 1. User validation
    # -------------------
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized user")

    if current_user.tenant_id != payload.tenant_id:
        raise HTTPException(status_code=403, detail="User not allowed for this tenant")

    # --------------------------------------------------
    # 2. Prevent creating logs for future dates/shifts
    # --------------------------------------------------
    today = date.today()
    now = datetime.now()

    if payload.date > today:
        raise HTTPException(status_code=400, detail="Cannot create entry for future date")

    # get shift timings
    shift = db.query(models.ShiftTiming).filter(
        models.ShiftTiming.id == payload.shift_time_id,
        models.ShiftTiming.tenant_id == payload.tenant_id
    ).first()

    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found for tenant")

    # Combine shift date with shift end_time to block future shifts
    shift_end = datetime.combine(payload.date, shift.end_time)
    if shift_end > now:
        raise HTTPException(status_code=400, detail="Cannot enter data for an advance shift")

    # --------------------------------------------------
    # 3. Validate Mold-Machine mapping belongs to tenant
    # --------------------------------------------------
    mold_machine = db.query(models.MoldMachine) \
        .join(models.Mold, models.Mold.id == models.MoldMachine.mold_id) \
        .join(models.Machine, models.Machine.id == models.MoldMachine.machine_id) \
        .filter(
            models.MoldMachine.id == payload.mold_machine_id,
            models.Mold.tenant_id == payload.tenant_id,
            models.Machine.tenant_id == payload.tenant_id
        ).first()

    if not mold_machine:
        raise HTTPException(status_code=404, detail="Invalid Mold-Machine mapping for this tenant")

    # --------------------------------------------------
    # 4. Prevent duplicate entry per tenant/date/shift/mold_machine
    # --------------------------------------------------
    existing_log = db.query(models.ProductionLog).filter(
        and_(
            models.ProductionLog.tenant_id == payload.tenant_id,
            models.ProductionLog.date == payload.date,
            models.ProductionLog.shift_time_id == payload.shift_time_id,
            models.ProductionLog.mold_machine_id == payload.mold_machine_id
        )
    ).first()

    if existing_log:
        raise HTTPException(
            status_code=400,
            detail="Duplicate entry already exists for this tenant/date/shift/mold-machine"
        )

    # --------------------------------------------------
    # 5. Insert Production Log
    # --------------------------------------------------
    new_log = models.ProductionLog(
        tenant_id=payload.tenant_id,
        operator=current_user.id,
        shift_time_id=payload.shift_time_id,
        date=payload.date,
        mold_machine_id=payload.mold_machine_id,
        actual=payload.actual,
        target=payload.target
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)

    # --------------------------------------------------
    # 6. Efficiency calculation
    # --------------------------------------------------
    efficiency = (payload.actual / payload.target * 100) if payload.target else 0

    # --------------------------------------------------
    # 7. Bulk Insert Downtime & Rejections (only if eff < 95%)
    # --------------------------------------------------
    if efficiency < 95:
        # ---- Downtimes ----
        if payload.downtime_entries:
            df_downtime = pd.DataFrame([{
                "tenant_id": payload.tenant_id,
                "production_log_id": new_log.id,
                "downtime_id": d.downtime_id,
                "duration_min": d.duration_min,
                "created_by": current_user.id
            } for d in payload.downtime_entries])

            # remove duplicates (tenant_id + production_log_id + downtime_id)
            df_downtime.drop_duplicates(
                subset=["tenant_id", "production_log_id", "downtime_id"],
                inplace=True
            )

            df_downtime.to_sql("production_downtime", db.bind, if_exists="append", index=False)

        # ---- Rejections ----
        if payload.defect_entries:
            df_rejection = pd.DataFrame([{
                "tenant_id": payload.tenant_id,
                "production_log_id": new_log.id,
                "defect_id": r.defect_id,
                "quantity": r.quantity
            } for r in payload.defect_entries])

            df_rejection.drop_duplicates(
                subset=["tenant_id", "production_log_id", "defect_id"],
                inplace=True
            )

            df_rejection.to_sql("production_rejection", db.bind, if_exists="append", index=False)

    return {
        "message": "Production log created successfully",
        "production_log_id": new_log.id,
        "efficiency": efficiency,
        "downtime_entries": len(payload.downtime_entries or []),
        "rejection_entries": len(payload.defect_entries or [])
    }