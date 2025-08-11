from typing import List
from fastapi import status,HTTPException,Depends,APIRouter
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import pandas as pd

from .. import schemas,oauth2,models
from ..function import admin, backtable,tenant,fetch_details,user,shifts_fn
from .. import utls
from ..database import get_db


router = APIRouter(
  prefix="/tenant/v1",tags=['tenant']
)

# Create User Start here (created on 29.7.2025 by Rajesh Bondgilwar) --------------------------->
@router.post("/create-user",status_code=status.HTTP_201_CREATED)
def create_user(user:schemas.CreateTenatUser,db:Session = Depends(get_db),current_user: int = Depends(oauth2.get_current_user)):
  try:
    user.employee_id = utls.employee_code(user.employee_id,current_user.tenant.tenant_code)
    user1= backtable.getUserByEmployeCode(user.employee_id,db)
    user_email = db.query(models.User).filter(
        models.User.tenant_id == current_user.tenant.id,
        models.User.email == user.email
    ).first()
    if user1:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"User already exists {user.user_name}") 
    if user_email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"User already exists {user.user_name}")


    tenant.user_role_admin(current_user)
    backtable.get_user_status(current_user)
    user.password = utls.hash(user.password)
    role = backtable.getRoleBycode(user.role,db)
    new_user = models.User(
      **user.model_dump(exclude={"role"}),
      tenant_id=current_user.tenant.id,
      role_id=role.id,
      created_by=current_user.id,
      updated_by=current_user.id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
      "status":"success",
      "user":schemas.UserOut.model_validate(new_user)
    }
  except HTTPException as he:
    raise he
  except SQLAlchemyError as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=str(e))
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=str(e))

# Create User Ends <---------------------------------( rev 0.0 dt 29.7.2025 by Rajesh Bondgilwar)


# Create Reset Password Start here (created on 29.7.2025 by Rajesh Bondgilwar) --------------------------->
@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(
    resetPassword: schemas.ResetPassword,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    try:
        # Get the user whose password needs to be changed
        user_2_change = backtable.getUserByEmployeCode(resetPassword.employee_id, db)

        if utls.verify(resetPassword.new_password,user_2_change.password):
           raise HTTPException(status_code=status.HTTP_302_FOUND,detail=f"Same password cant be changed , Please provide diffrent password!!!")

        if not user_2_change:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Verify if current user is admin
        tenant.user_role_admin(current_user)

        # Check if user belongs to the same tenant
        if user_2_change.tenant.tenant_code != current_user.tenant.tenant_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"You are not authorized to change the password for {user_2_change.tenant.tenant_name} users"
            )

        # Update password
        user_2_change.password = utls.hash(resetPassword.new_password)
        user_2_change.updated_by = current_user.id
        db.commit()
        db.refresh(user_2_change)

        return {"message": "Password reset successfully"}

    except HTTPException as he:
        raise he
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


# Create User Ends <---------------------------------( rev 0.0 dt 29.7.2025 by Rajesh Bondgilwar)

# Tenant Shift Start here (created on 29.7.2025 by Rajesh Bondgilwar) --------------------------->

@router.post("/bulk", status_code=status.HTTP_201_CREATED)
def create_multiple_shifts(
    payload: List[schemas.TenantShiftCreate],
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    try:
        # Validate user
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)

        # Validate tenant
        user_tenant = db.query(models.Tenant).filter(
            models.Tenant.tenant_code == current_user.tenant.tenant_code
        ).first()
        if not user_tenant:
            raise HTTPException(403, detail="You are not authorized to create shifts for this tenant")

        created_shifts = []
        skipped_shifts = []

        for shift in payload:
            if not shift.timings:
                raise HTTPException(400, "Shift timings must be provided")

            # Check if shift already exists
            exists_shift = db.query(models.TenantShift).filter_by(
                tenant_id=user_tenant.id, shift_name=shift.shift_name
            ).first()

            if exists_shift:
                skipped_shifts.append(shift.shift_name)
                continue  # Skip if shift exists

            # Auto-assign weekdays if missing
            for idx, t in enumerate(shift.timings):
                if t.weekday is None:
                    t.weekday = (idx % 7) + 1  # 1–7 (Monday–Sunday)

            # Validate no duplicate weekdays in same shift
            weekdays = [t.weekday for t in shift.timings]
            if len(weekdays) != len(set(weekdays)):
                raise HTTPException(400, f"Duplicate weekday found in shift '{shift.shift_name}'")

            # Check overlaps in the same shift
            shifts_fn.check_overlap(shift.timings)

            # Calculate new shift hours
            new_hours = {}
            for t in shift.timings:
                dur = shifts_fn.calculate_duration(t.shift_start.strftime("%H:%M"), t.shift_end.strftime("%H:%M"))
                new_hours[t.weekday] = new_hours.get(t.weekday, 0) + dur

            # Get existing shift durations for tenant
            existing_hours = {}
            existing_timings = (
                db.query(models.ShiftTiming)
                .join(models.TenantShift, models.TenantShift.id == models.ShiftTiming.tenant_shift_id)
                .filter(models.TenantShift.tenant_id == user_tenant.id)
                .all()
            )
            for s in existing_timings:
                dur = shifts_fn.calculate_duration(s.shift_start.strftime("%H:%M"), s.shift_end.strftime("%H:%M"))
                existing_hours[s.weekday] = existing_hours.get(s.weekday, 0) + dur

            # Validate total hours <= 24
            for weekday, hours in new_hours.items():
                total = existing_hours.get(weekday, 0) + hours
                if total > 24:
                    raise HTTPException(
                        400,
                        f"Total shift duration exceeds 24 hours on weekday {weekday} for tenant '{user_tenant.tenant_name}'"
                    )

            # Create new shift
            new_shift = models.TenantShift(
                tenant_id=user_tenant.id,
                shift_name=shift.shift_name,
                created_by=current_user.id,
                updated_by=current_user.id
            )
            db.add(new_shift)
            db.flush()

            # Add shift timings
            for t in shift.timings:
                new_timing = models.ShiftTiming(
                    tenant_shift_id=new_shift.id,
                    weekday=t.weekday,
                    shift_start=t.shift_start,
                    shift_end=t.shift_end,
                    created_by=current_user.id,
                    updated_by=current_user.id
                )
                db.add(new_timing)

            created_shifts.append(shift.shift_name)

        db.commit()

        return {
            "message": "Shifts processed successfully",
            "created": created_shifts,
            "skipped": skipped_shifts
        }

    except HTTPException as he:
        raise he
    except SQLAlchemyError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"SQL Server Error: {str(e)}")
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {str(e)}")


# @router.post("/bulk", status_code=status.HTTP_201_CREATED)
# def create_multiple_shifts(
#     payload: List[schemas.TenantShiftCreate],
#     db: Session = Depends(get_db),
#     current_user: int = Depends(oauth2.get_current_user)
# ):
#     try:
#         # Validate user
#         user.get_user_status(current_user)
#         tenant.user_role_admin(current_user)
    

#         # Validate tenant
#         user_tenant = db.query(models.Tenant).filter(
#             models.Tenant.tenant_code == current_user.tenant.tenant_code
#         ).first()
#         if not user_tenant:
#             raise HTTPException(
#                 403, detail=f"You are not authorized to create shifts for this tenant"
#             )

#         for shift in payload:
#             if not shift.timings:
#                 raise HTTPException(400, "Shift timings must be provided")

#             # Check if shift already exists
#             exists_shift = db.query(models.TenantShift).filter_by(
#                 tenant_id=user_tenant.id, shift_name=shift.shift_name
#             ).first()
#             if exists_shift:
#                 raise HTTPException(
#                     409,
#                     f"Shift '{shift.shift_name}' already exists for tenant '{user_tenant.tenant_name}'"
#                 )

#             # 🚫 Validate no duplicate weekdays
#             weekdays = [t.weekday for t in shift.timings]
#             if len(weekdays) != len(set(weekdays)):
#                 raise HTTPException(400, f"Duplicate weekday found in shift '{shift.shift_name}'")

#             # ✅ Check internal overlaps
#             shifts_fn.check_overlap(shift.timings)

#             # 🕒 Calculate total shift hours for new shift
#             new_hours = {}
#             for t in shift.timings:
#                 dur = shifts_fn.calculate_duration(t.shift_start, t.shift_end)
#                 new_hours[t.weekday] = new_hours.get(t.weekday, 0) + dur

#             # 🔎 Get existing shift durations from DB
#             existing_hours = {}
#             existing_timings = (
#                 db.query(models.ShiftTiming)
#                 .join(models.TenantShift, models.TenantShift.id == models.ShiftTiming.tenant_shift_id)
#                 .filter(models.TenantShift.tenant_id == user_tenant.id)
#                 .all()
#             )
#             for s in existing_timings:
#                 dur = shifts_fn.calculate_duration(s.shift_start, s.shift_end)
#                 existing_hours[s.weekday] = existing_hours.get(s.weekday, 0) + dur

#             # Validate total hours <= 24
#             for weekday, hours in new_hours.items():
#                 total = existing_hours.get(weekday, 0) + hours
#                 if total > 24:
#                     raise HTTPException(
#                         400,
#                         f"Total shift duration exceeds 24 hours on weekday {weekday} for tenant '{user_tenant.tenant_name}'"
#                     )

#             # Create new shift
#             new_shift = models.TenantShift(
#                 tenant_id=user_tenant.id,
#                 shift_name=shift.shift_name,
#                 created_by=current_user.id,
#                 updated_by=current_user.id
#             )
#             db.add(new_shift)
        
#             db.flush()

#             # Add shift timings
#             for t in shift.timings:
#                 new_timing = models.ShiftTiming(
#                     tenant_shift_id=new_shift.id,
#                     weekday=t.weekday,
#                     shift_start=t.shift_start,
#                     shift_end=t.shift_end,
#                     created_by=current_user.id,
#                     updated_by=current_user.id
#                 )
#                 db.add(new_timing)

#         # ✅ Commit after processing all shifts
#         db.commit()

#         return {"message": "Shifts created successfully"}

#     except HTTPException as he:
#         raise he
#     except SQLAlchemyError as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"SQL Server Error: {str(e)}"
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Internal Server Error: {str(e)}"
#         )

# # Tenant Shift Start here <---------------------------------( rev 0.0 dt 29.7.2025 by Rajesh Bondgilwar)

