from sqlalchemy import (
    Column, DateTime, Enum, Integer, String, Boolean, ForeignKey, Float, BigInteger,
    Sequence, Date, Time, UniqueConstraint, Index, func
)
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from .database import Base
from sqlalchemy.dialects.postgresql import JSONB

# <-------------------------- Role Table starts
class UserRole(Base):
    __tablename__ = "user_role"
    id = Column(Integer, primary_key=True, nullable=False)
    user_role = Column(String, nullable=False, unique=True)
    created_by=Column(Integer)
    updated_by=Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    


    # Relarionship 
    users = relationship("User", back_populates="role") 
# ---------------------------> Role table ends

# <-------------------------- Tenant table starts
class Tenant(Base):
    __tablename__ = "tenant"
    id = Column(Integer, primary_key=True, nullable=False)
    tenant_name = Column(String, nullable=False)
    tenant_code = Column(String,nullable=False,unique=True)
    address = Column(String, nullable=False)
    is_verified = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by=Column(Integer)
    updated_by=Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
  

    # Relarionship 
    users = relationship("User", back_populates="tenant",cascade="all, delete-orphan")
    shifts = relationship("TenantShift", back_populates="tenant",cascade="all, delete-orphan")
    operations = relationship("Operation", back_populates="tenant",cascade="all, delete-orphan")
    defects = relationship("Defect", back_populates="tenant",cascade="all, delete-orphan")
    down_times = relationship("DownTime", back_populates="tenant", cascade="all, delete-orphan")
    department = relationship("Department", back_populates="tenant", cascade="all, delete-orphan")  
    department_users = relationship("DepartmentUser", back_populates="tenant", cascade="all, delete-orphan")  
    products = relationship("Product",back_populates="tenant", cascade="all, delete-orphan")
    machines = relationship("Machine", back_populates="tenant", cascade="all, delete-orphan")
    molds = relationship("Mold", back_populates="tenant", cascade="all, delete-orphan")

   
# ---------------------------> Tenant table ends


# <-------------------------- User table starts
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenant.id', ondelete='CASCADE'), nullable=False)
    role_id = Column(Integer, ForeignKey('user_role.id', ondelete="CASCADE"), nullable=False)
    employee_id = Column(String, nullable=False)
    user_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    password = Column(String,nullable=False)
    is_verified = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(Integer)
    updated_by = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


    # Relationships
    role = relationship("UserRole", back_populates="users")
    tenant = relationship("Tenant", back_populates="users")
    department_users = relationship("DepartmentUser", back_populates="users", cascade="all, delete-orphan")
    inspection_result = relationship("ProductInspectionResult", back_populates="users", cascade="all, delete-orphan")


    __table_args__ = (
        UniqueConstraint('tenant_id','employee_id',name='uix_tenant_employee'),
        UniqueConstraint('tenant_id', 'email', name='uix_tenant_email'),
        Index('idx_tenant_id', 'tenant_id', 'user_name','employee_id'),
    )

# ---------------------------> User table ends

# <-------------------------- Tenant Shift table starts
class TenantShift(Base):
    __tablename__ = 'tenant_shift'
    id = Column(Integer, primary_key=True, nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenant.id', ondelete='CASCADE'), nullable=False)
    shift_name = Column(String, nullable=False)
    created_by=Column(Integer)
    updated_by=Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="shifts")
    timings = relationship("ShiftTiming", back_populates="tenant_shift", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('tenant_id','shift_name',name='uix_tenant_shift'),
    )


# ---------------------------> Tenant Shift table ends

# <-------------------------- ShiftTiming table starts 

class ShiftTiming(Base):
    __tablename__ = "shift_timing"

    id = Column(Integer, primary_key=True, index=True)
    tenant_shift_id = Column(Integer, ForeignKey("tenant_shift.id", ondelete="CASCADE"), nullable=False)
    shift_start = Column(Time, nullable=False)
    shift_end = Column(Time, nullable=False)
    weekday = Column(Integer, nullable=True)  # 0 = Monday ... 6 = Sunday
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    tenant_shift = relationship("TenantShift", back_populates="timings")


    inspection_result = relationship("ProductInspectionResult", back_populates="shifts_timings", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('tenant_shift_id', 'weekday', name='uix_shift_timing'),
    )


# ---------------------------> ShiftTiming table ends

# <-------------------------- Operation table starts 
class Defect(Base):
    __tablename__ = "defect"
    id = Column(Integer, primary_key=True, nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenant.id', ondelete='CASCADE'), nullable=False)
    defect_name = Column(String, nullable=False)
    created_by = Column(Integer)
    updated_by = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="defects")
    defect_departments = relationship("DefectDepartment", back_populates="defects", cascade="all, delete-orphan")
   
  

    __table_args__ = (
        UniqueConstraint('tenant_id', 'defect_name', name='uix_tenant_defect'),
    )


# <-------------------------- Defect table starts 
class DownTime(Base):
    __tablename__ = "down_time"
    id = Column(Integer, primary_key=True, nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenant.id', ondelete='CASCADE'), nullable=False)
    downtime_name = Column(String, nullable=False)
    created_by = Column(Integer)
    updated_by = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="down_times")
    downtime_departments = relationship("DownTimeDepartment", back_populates="downtime", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'downtime_name', name='uix_tenant_down_time'),
    )



# ---------------------------> Defect table ends

# <-------------------------- Operatiom table starts 
class Operation(Base):
    __tablename__ = "operation"
    id = Column(Integer, primary_key=True, nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenant.id', ondelete='CASCADE'), nullable=False)
    operation_name = Column(String, nullable=False)
    created_by = Column(Integer)
    updated_by = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="operations")
    product_operations = relationship("ProductOperationSequence", back_populates="operations", cascade="all, delete-orphan")
    operation_departments = relationship("OperationDepartment", back_populates="operation", cascade="all, delete-orphan")
    
   

    __table_args__ = (
        UniqueConstraint('tenant_id', 'operation_name', name='uix_tenant_operation'),
    )

# ---------------------------> Operation table ends

# <-------------------------- Operation Department table starts
class OperationDepartment(Base):
    __tablename__ = "operation_department"
    id = Column(Integer, primary_key=True, nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    operation_id = Column(Integer, ForeignKey("operation.id", ondelete="CASCADE"), nullable=False)
    department_id = Column(Integer, ForeignKey("department.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(Integer)
    updated_by = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    tenant = relationship("Tenant")
    operation = relationship("Operation", back_populates="operation_departments")
    department = relationship("Department", back_populates="operation_departments")

    __table_args__ = (
        UniqueConstraint("tenant_id", "operation_id", "department_id", name="uix_tenant_operation_department"),
    )
# ---------------------------> Operation Departmenttable ends
class DefectDepartment(Base):
    __tablename__ = "defect_department"
    id = Column(Integer, primary_key=True, nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    defect_id = Column(Integer, ForeignKey("defect.id", ondelete="CASCADE"), nullable=False)
    department_id = Column(Integer, ForeignKey("department.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(Integer)
    updated_by = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    tenant = relationship("Tenant")
    defects = relationship("Defect", back_populates="defect_departments")
    department = relationship("Department", back_populates="defect_departments")

    __table_args__ = (
        UniqueConstraint("tenant_id", "defect_id", "department_id", name="uix_tenant_defect_department"),
    )


class DownTimeDepartment(Base):
    __tablename__ = "downtime_department"
    id = Column(Integer, primary_key=True, nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    downtime_id = Column(Integer, ForeignKey("down_time.id", ondelete="CASCADE"), nullable=False)
    department_id = Column(Integer, ForeignKey("department.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(Integer)
    updated_by = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    tenant = relationship("Tenant")
    downtime = relationship("DownTime", back_populates="downtime_departments")
    department = relationship("Department", back_populates="downtime_departments")

    __table_args__ = (
        UniqueConstraint("tenant_id", "downtime_id", "department_id", name="uix_tenant_downtime_department"),
    )


# <-------------------------- Department table starts -------------------------->
class Department(Base):
    __tablename__ = "department"
    id = Column(Integer, primary_key=True, nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenant.id', ondelete='CASCADE'), nullable=False)
    department_name = Column(String, nullable=False)
    created_by = Column(Integer)
    updated_by = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="department")  
    department_users = relationship("DepartmentUser", back_populates="department", cascade="all, delete-orphan")
    operation_departments = relationship("OperationDepartment", back_populates="department", cascade="all, delete-orphan")
    defect_departments = relationship("DefectDepartment", back_populates="department", cascade="all, delete-orphan")
    downtime_departments = relationship("DownTimeDepartment", back_populates="department", cascade="all, delete-orphan")
 

  

    __table_args__ = (
        UniqueConstraint('tenant_id', 'department_name', name='uix_tenant_department'),
    )
# <-------------------------- Department table ends -------------------------->

# <-------------------------- Department User table starts -------------------------->
class DepartmentUser(Base):
    __tablename__ = "department_user"
    id = Column(Integer, primary_key=True, nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenant.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    department_id = Column(Integer, ForeignKey('department.id', ondelete='CASCADE'), nullable=False)
    created_by = Column(Integer)
    updated_by = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="department_users")
    users = relationship("User", back_populates="department_users")
    department = relationship("Department", back_populates="department_users")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'user_id', 'department_id', name='uix_tenant_user_department'),
    )
# <-------------------------- Department User table ends -------------------------->

# <-------------------------- Product  table starts -------------------------->
class Product(Base):
    __tablename__ = "product"
    id = Column(Integer,primary_key=True,nullable=False)
    tenant_id = Column(Integer,ForeignKey('tenant.id',ondelete='CASCADE'),nullable=False)
    product_name = Column(String,nullable=False)
    product_no = Column(String,nullable=False)
    created_by = Column(Integer)
    updated_by = Column(Integer)
    created_at = Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    updated_at = Column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now(),nullable=False)

    # Relationships
    tenant = relationship("Tenant",back_populates="products")
    product_drawings = relationship("ProductDrawing", back_populates="products", cascade="all, delete-orphan")
    product_operations = relationship("ProductOperationSequence", back_populates="products", cascade="all, delete-orphan")
    # inspections = relationship("ProductInspection", back_populates="products", cascade="all, delete-orphan")
    product_molds = relationship("ProductMold", back_populates="products", cascade="all, delete-orphan")



    __table_args__ = (
        UniqueConstraint('tenant_id','product_no',name='uix_tenant_product_no'),
        UniqueConstraint('tenant_id', 'product_name', name='uix_tenant_product_name'),
    )

# <-------------------------- Product  table ends -------------------------->


# <-------------------------- Product Drawing  table Starts -------------------------->
class ProductDrawing(Base):
    __tablename__ = "product_drawing"
    id = Column(Integer, primary_key=True, nullable=False)
    product_id = Column(Integer, ForeignKey('product.id', ondelete='CASCADE'), nullable=False)
    drawing_no = Column(String, nullable=False)
    created_by = Column(Integer)
    updated_by = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    products = relationship("Product", back_populates="product_drawings")
    inspection = relationship("ProductInspection",back_populates="product_drawings",cascade="all, delete-orphan")
    

    # product_molds = relationship("ProductMold", back_populates="product_drawings")

    __table_args__ = (
        UniqueConstraint('product_id', 'drawing_no', name='uix_product_drawing_no'),
    )

# <-------------------------- Product Drawing Ends -------------------------->

# <-------------------------- Product Operation  table Starts -------------------------->

class ProductOperationSequence(Base):
    __tablename__ = "product_operation_sequence"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('product.id', ondelete='CASCADE'), nullable=False)
    operation_id = Column(Integer, ForeignKey('operation.id', ondelete='CASCADE'), nullable=False)
    sequence_no = Column(Integer, nullable=False)  # 1, 2, 3 for order of operations
    created_by = Column(Integer)
    updated_by = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    products = relationship("Product", back_populates="product_operations")
    operations = relationship("Operation", back_populates="product_operations")

    __table_args__ = (
        UniqueConstraint('product_id', 'operation_id', name='uix_product_operation'),
        UniqueConstraint('product_id', 'sequence_no', name='uix_product_sequence'),
    )


# <-------------------------- Product Operation  table Ends -------------------------->

# <-------------------------- Product Inspection  table Starts -------------------------->
class ProductInspection(Base):
    __tablename__ = "product_inspection"

    id = Column(Integer, primary_key=True, index=True)
    drawing_id = Column(Integer, ForeignKey('product_drawing.id', ondelete='CASCADE'), nullable=False)
    dimension_name = Column(String, nullable=False)
    inspection_type = Column(Enum("dimensional", "gauge", name="inspection_type_enum"), nullable=False)
    # For dimensional inspection
    lower_limit = Column(Float, nullable=True)
    upper_limit = Column(Float, nullable=True)
    unit = Column(String, nullable=True)

    # For gauge inspection
    gauge_name = Column(String, nullable=True)

    created_by = Column(Integer)
    updated_by = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product_drawings = relationship("ProductDrawing", back_populates="inspection")
    inspection_result = relationship("ProductInspectionResult", back_populates="inspection", cascade="all, delete-orphan")
    

    __table_args__ = (
        UniqueConstraint('drawing_id', 'dimension_name', name='uix_product_dimension'),
    )



# <-------------------------- Product Inspection  table Ends -------------------------->

# <-------------------------- Product Inspection Result table Starts -------------------------->

class ProductInspectionResult(Base):
    __tablename__ = "product_inspection_result"

    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey('product_inspection.id', ondelete='CASCADE'), nullable=False)
    inspector_id = Column(Integer, ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    shift_timingid = Column(Integer, ForeignKey('shift_timing.id', ondelete='SET NULL'), nullable=True)

    measured_value = Column(Float, nullable=True)
    go_no_go = Column(Boolean, nullable=True)

    # New fields for date + hour tracking
    inspection_date = Column(Date, nullable=False)  # only the date
    inspection_hour = Column(Integer, nullable=False)  # 0–23

    created_by = Column(Integer)
    updated_by = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    inspection = relationship("ProductInspection", back_populates="inspection_result")
    users = relationship("User", back_populates="inspection_result")
    shifts_timings = relationship("ShiftTiming", back_populates="inspection_result")

    __table_args__ = (
        UniqueConstraint('shift_timingid', 'inspection_date', 'inspection_hour', name='uix_shift_hourly_unique'),
    )


# class ProductInspectionResult(Base):
#     __tablename__ = "product_inspection_result"

#     id = Column(Integer, primary_key=True, index=True)
#     inspection_id = Column(Integer, ForeignKey('product_inspection.id', ondelete='CASCADE'), nullable=False)
#     inspector_id = Column(Integer, ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
#     shift_timingid = Column(Integer, ForeignKey('shift_timing.id', ondelete='SET NULL'), nullable=True)
    

#     # For dimensional inspection
#     measured_value = Column(Float, nullable=True)

#     # For gauge inspection
#     go_no_go = Column(Boolean, nullable=True)

#     # timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

#     created_by = Column(Integer)
#     updated_by = Column(Integer)
#     created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

#     inspection = relationship("ProductInspection", back_populates="inspection_result")
#     users = relationship("User",back_populates="inspection_result")
#     shifts_timings = relationship("ShiftTiming",back_populates="inspection_result")

#     __table_args__ = (
#         UniqueConstraint('inspection_id', 'timestamp', name='uix_inspection_timestamp'),
#     )



# <-------------------------- Product Inspection Result table Ends -------------------------->


# <-------------------------- Mold table starts here-------------------------->
class Mold(Base):
    __tablename__ = "mold"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey('tenant.id', ondelete='CASCADE'), nullable=False)
    mold_no = Column(String, nullable=False)
    description = Column(String, nullable=True)
    cavities = Column(Integer, nullable=False)
    special_notes = Column(JSONB, nullable=True)
    created_by = Column(Integer)
    updated_by = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    tenant = relationship("Tenant", back_populates="molds")
    product_molds = relationship("ProductMold", back_populates="mold", cascade="all, delete-orphan")
    mold_machines = relationship("MoldMachine", back_populates="mold", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'mold_no', name='uix_tenant_mold_no'),
    )

# <-------------------------- Mold table Ends    here-------------------------->
# <-------------------------- Product Mold table starts here-------------------------->
class ProductMold(Base):
    __tablename__ = "product_mold"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('product.id', ondelete='CASCADE'), nullable=False)
    mold_id = Column(Integer, ForeignKey('mold.id', ondelete='CASCADE'), nullable=False)
    created_by = Column(Integer)
    updated_by = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    products = relationship("Product", back_populates="product_molds")
    mold = relationship("Mold", back_populates="product_molds")
    __table_args__ = (
        UniqueConstraint('product_id', 'mold_id', name='uix_product_mold'), 
    )
# <-------------------------- Product Mold table Ends here-------------------------->
# <-------------------------- Machine Table table starts here-------------------------->
class Machine(Base):
    __tablename__ = "machine"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey('tenant.id', ondelete='CASCADE'), nullable=False)
    machine_code = Column(String, nullable=False)  # Unique machine identifier for a tenant
    description = Column(String, nullable=True)
    capacity = Column(String, nullable=True)
      # e.g., 120T, 200T (optional)
    special_notes = Column(JSONB, nullable=True)
    created_by = Column(Integer)
    updated_by = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="machines")
    mold_machines = relationship("MoldMachine", back_populates="machines", cascade="all, delete-orphan")



    __table_args__ = (
        UniqueConstraint('tenant_id', 'machine_code', name='uix_tenant_machine_code'),
    )

# <-------------------------- Machine Table Ends here-------------------------->
# <-------------------------- Mold Machine Table starts here-------------------------->
class MoldMachine(Base):
    __tablename__ = "mold_machine"

    id = Column(Integer, primary_key=True, index=True)
    mold_id = Column(Integer, ForeignKey('mold.id', ondelete='CASCADE'), nullable=False)
    machine_id = Column(Integer, ForeignKey('machine.id', ondelete='CASCADE'), nullable=False)

    # Relationships
    mold = relationship("Mold", back_populates="mold_machines")
    machines = relationship("Machine", back_populates="mold_machines")
    created_by = Column(Integer)
    updated_by = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('mold_id', 'machine_id', name='uix_mold_machine'),
    )

# <-------------------------- Mold Machine Table ends here-------------------------->