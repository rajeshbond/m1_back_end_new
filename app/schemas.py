
from datetime import datetime , date, time
from operator import le
from pydantic import BaseModel, EmailStr, Field , conint
from typing import Any, Dict, List, Literal, Optional, Union
from app.models import *
from pydantic.types import conlist
from pydantic import BaseModel, Field, field_validator
from zoneinfo import ZoneInfo
from app.function import timeapp

class RoleCreate(BaseModel):
    user_role:str

class ChangeRole(BaseModel):
    user_role:str
    change_role:str
class RoleOut(BaseModel):
    id:int
    user_role:str
    
    model_config = {
    "from_attributes": True
    }

class TenantCreate(BaseModel):
    tenant_name:str
    tenant_code:str
    address:str

class Tenantout(BaseModel):
    id:int
    tenant_name:str
    tenant_code:str
    is_verified:bool

    model_config = {
    "from_attributes": True
    }
       

class UserCreate(BaseModel):
    employee_id: str
    user_name:str
    tenant_code: Optional[str] = Field(default='info')
    phone:str
    role:str
    email:EmailStr
    password:str
class CreateTenatUser(BaseModel):
    employee_id: str
    user_name:str
    phone:str
    role:str
    email:EmailStr
    password:str

class UserfirstCreate(BaseModel):
    employee_id: Optional[str] = Field(default= "01")
    user_name:str
    phone:str
    email:EmailStr
    password:str

class CreateAdminTenant(BaseModel):
    tenant:TenantCreate
    user:UserfirstCreate


class UserOut(BaseModel):
    id:int
    email:EmailStr
    role:RoleOut
    tenant:Tenantout
    employee_id:str
    user_name:str
    is_verified:bool
    is_active:bool

    model_config = {
    "from_attributes": True
    }
class SetupSuperAdmin(BaseModel):
    role:RoleCreate
    tenant:TenantCreate
    user:UserfirstCreate

class UpdateTenant(BaseModel):
    tenant_code: Optional[str]
    tenant_name: Optional[str]
    address: Optional[str]
    is_verified: Optional[bool]
    is_active: Optional[bool]

class UpdateUser(BaseModel):
    user_name: Optional[str]
    phone: Optional[str]
    email: Optional[EmailStr]
    is_verified: Optional[bool]
    is_active: Optional[bool]

class ChangePassword(BaseModel):
    employee_id: str
    old_password: str
    new_password: str

class UserChangePassword(BaseModel):
    old_password: str
    new_password: str




class userTenantResetPassword(BaseModel):
    old_password: str
    new_password: str

class ResetPassword(BaseModel):
    employee_id: str
    new_password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    

class TokenData(BaseModel):
    id: Optional[str] = None

class UserDepartment(BaseModel):
    employee_code: str
    department : List[str]

class ShiftTimingCreate(BaseModel):
    shift_start: time = Field(..., example="08:00")
    shift_end: time = Field(..., example="16:00")
    weekday: Optional[int] = None ##= Field(..., ge=1, le=7, example=1) # 1 = Monday to 7 = Sunday

class TenantShiftCreate(BaseModel):
    tenant_code: str
    shift_name: str
    timings: List[ShiftTimingCreate]    

class TenantDownTime(BaseModel):
    tenant_code: str
    downTime: List[str]

class TenantDefect(BaseModel):
    tenant_code: str
    defect: List[str]

class TenantDepartment(BaseModel):
    tenant_code: str
    department: List[str] # or List[YourOperationModel] if you have a nested schema

class TenantOperation(BaseModel):
    tenant_code: str
    operation: List[str] # or List[YourOperationModel] if you have a nested schema

# class TenantOperation(BaseModel):
#     tenant_code: str = Field(..., description="Tenant unique code")
#     department_id: int = Field(..., description="Department ID under which the operations are created")
#     operation: List[str] = Field(..., description="List of operation names to be added")

class DepartmentOperation(BaseModel):
    department_id: int = Field(..., description="Department ID")
    operation: List[str] = Field(..., description="List of operation names")

class TenantOperationBulk(BaseModel):
    tenant_code: str = Field(..., description="Tenant unique code")
    departments: List[DepartmentOperation] = Field(..., description="List of departments with operations")

class TenantOperationResponse(BaseModel):
    status: str
    inserted_operations: List[str]

class TenantDefect(BaseModel):
    tenant_code: str
    defect: List[str] # or List[YourOperationModel] if you have a nested schema

class TenantDownTime(BaseModel):
    tenant_code: str
    down_time: List[str] # or List[YourOperationModel] if you have a nested schema

class TenantDepartment(BaseModel):
    tenant_code: str
    department: List[str]


class EditTenantDepartment(BaseModel):
    tenant_code: str
    department_name: str
    new_department_name: str



# ------------------------------------------------------

class OperationDepartmentEntry(BaseModel):
    operation_name: str
    department_names: List[str]

class TenantOperationDepartment(BaseModel):
    tenant_code: str
    operations: List[OperationDepartmentEntry]



class DefectDepartmentEntry(BaseModel):
    department_names: Union[str, List[str]]  # can be "molding" or ["molding", "painting"]
    defect_names: List[str]  # always a list, e.g., ["shortmolding", "flash"]

# Main request schema
class TenantDefectDepartment(BaseModel):
    tenant_code: str
    defect: List[DefectDepartmentEntry]  # list of entries


class DownDepartmentEntry(BaseModel):
    department_names: Union[str, List[str]]  # can be "molding" or ["molding", "painting"]
    downtime_names: List[str]  # always a list, e.g., ["shortmolding", "flash"]

# Main request schema
class TenantDownTimeDepartment(BaseModel):
    tenant_code: str
    downtime: List[DownDepartmentEntry]  # list of entries

# ------- Products 

class ProductBase(BaseModel):
    product_name: str = Field(..., example="Widget A")
    product_no: str = Field(..., example="PRD-001")

# Create Schema
class ProductCreate(ProductBase):
    pass

# Update Schema
class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    product_no: Optional[str] = None

# Response Schema
class ProductResponse(ProductBase):
    id: int
    tenant_id: int
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: datetime
    updated_at: datetime


    model_config = {
    "from_attributes": True
    }

# ---------- PRODUCT DRAWING ----------
class ProductDrawingBase(BaseModel):
    product_id: int
    drawing_no: str

class ProductDrawingCreate(ProductDrawingBase):
    pass

class ProductDrawingUpdate(BaseModel):
    drawing_no: str

class ProductDrawingResponse(ProductDrawingBase):
    id: int
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {
    "from_attributes": True
    }


# ---------- PRODUCT OPERATION ----------
class ProductOperationBase(BaseModel):
    product_id: int
    operation_id: int
    sequence_no: int
    

class ProductOperationCreate(BaseModel):
    operation_name: str = Field(..., description="Name of the operation, must exist in the Operation table")
    sequence_no: int = Field(..., description="Sequence number for the operation in the product workflow")

class ProductOperationBulkCreate(BaseModel):
    product_id: int = Field(..., description="ID of the product to which operations will be assigned")
    operations: List[ProductOperationCreate] = Field(..., description="List of operations for this product")

class ProductOperationUpdate(BaseModel):
    operation_id: int
    sequence_no: int

class ProductOperationResponse(ProductOperationBase):
    id: int
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {
    "from_attributes": True
    }

# class ProductOperationBulkCreate(BaseModel):
#     operations: List[ProductOperationCreate]  # Each has product_id, operation_id, sequence_no

class OperationSequenceUpdateItem(BaseModel):
    operation_name: str = Field(..., description="Operation name to reorder")
    sequence_no: int = Field(..., ge=1, description="New sequence number")

class ProductOperationSequenceReorder(BaseModel):
    product_id: int = Field(..., description="ID of the product")
    operations: List[OperationSequenceUpdateItem]


# -------------------------
# Base schema Product Instaection 
# -------------------------
class InspectionItem(BaseModel):
    dimension_name: str = Field(..., example="Length")
    inspection_type: Literal["dimensional", "gauge"] = Field(..., example="dimensional")
    lower_limit: Optional[float] = Field(None, example=1.0)
    upper_limit: Optional[float] = Field(None, example=2.0)
    unit: Optional[str] = Field(None, example="mm")
    gauge_name: Optional[str] = Field(None, example="Vernier")

class ProductInspectionBulkCreate(BaseModel):
    drawing_id: int = Field(..., example=1)
    inspections: List[InspectionItem]

class ProductInspectionResponse(BaseModel):
    id: int
    drawing_id: int
    dimension_name: str
    inspection_type: str
    lower_limit: Optional[float]
    upper_limit: Optional[float]
    unit: Optional[str]
    gauge_name: Optional[str]
    created_by: Optional[int]
    updated_by: Optional[int]

    model_config = {
    "from_attributes": True
    }

class ProductInspectionUpdate(BaseModel):
    dimension_name: Optional[str] = None
    inspection_type: Optional[Literal["dimensional", "gauge"]] = None
    lower_limit: Optional[float] = None
    upper_limit: Optional[float] = None
    unit: Optional[str] = None
    gauge_name: Optional[str] = None

class ProductInspectionResultBase(BaseModel):
    inspection_id: int
    inspector_id: Optional[int] = None
    shift_timingid: Optional[int] = None
    measured_value: Optional[float] = None
    go_no_go: Optional[bool] 
    inspection_date: date = Field(default_factory=date.today)
    inspection_hour: Optional[int] = Field(default_factory=lambda: datetime.now(tz=ZoneInfo("Asia/Kolkata")).hour, ge=0, le=23)




# class ProductInspectionResultBase(BaseModel):
#     inspection_id: int
#     inspector_id: Optional[int] = None
#     shift_timingid: Optional[int] = None
#     measured_value: Optional[float] = None
#     go_no_go: Optional[bool] = None
#     inspection_date: date
#     inspection_hour: Optional[int] = datetime.now(tz=ZoneInfo("Asia/Kolkata")).hour

class ProductInspectionResultCreate(ProductInspectionResultBase):
    pass

class ProductInspectionResultUpdate(BaseModel):
    inspector_id: Optional[int] = None
    shift_timingid: Optional[int] = None
    measured_value: Optional[float] = None
    go_no_go: Optional[bool] = None
    inspection_date: Optional[date] = None
    inspection_hour: Optional[int] = Field(None, ge=0, le=23)

class ProductInspectionResultResponse(ProductInspectionResultBase):
    id: int
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {
    "from_attributes": True
    }

class MoldBase(BaseModel):
    mold_no: str
    cavities: int = Field(..., ge=1)
    description: Optional[str] = None
    special_notes: Optional[Dict[str, Any]] = None

class MoldCreate(MoldBase):
    pass

class MoldUpdate(MoldBase):
    pass

class MoldCreateResponse(BaseModel):
    message: str
    mold: MoldBase

class MachineBase(BaseModel):
    machine_code: str
    description: Optional[str] = None
    capacity: Optional[str] = None
    special_notes: Optional[Any] = None  # JSONB can be dict/list

class MachineCreate(MachineBase):
    pass
    # tenant_id: int
    # created_by: Optional[int] = None

class MachineUpdate(MachineBase):
    updated_by: Optional[int] = None

class MachineOut(MachineBase):
    id: int
    tenant: Tenantout
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {
    "from_attributes": True
    }


class ProductMoldBase(BaseModel):
    product_name: str
    mold_no: str

class ProductMoldCreate(ProductMoldBase):
    pass

class ProductMoldUpdate(ProductMoldBase):
    pass

class ProductMoldOut(ProductMoldBase):
    id: int
    model_config = {
    "from_attributes": True
    }

class MoldMachineBase(BaseModel):
    mold_no: str
    machine_code: str

class MoldMachineCreate(MoldMachineBase):
    pass

class MoldMachineUpdate(MoldMachineBase):
    pass

class MoldMachineOut(BaseModel):
    id: int
    mold_id: int
    machine_id: int
    created_by: int
    updated_by: int

    model_config = {
    "from_attributes": True
    }