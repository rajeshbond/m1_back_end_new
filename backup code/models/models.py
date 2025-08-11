from sqlalchemy import (
    Column, DateTime, Integer, String, Boolean, ForeignKey, Float, BigInteger,
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
    users = relationship("User", back_populates="tenant")
    shifts = relationship("TenantShift", back_populates="tenant")
    operations = relationship("Operation", back_populates="tenant")
    defects = relationship("Defect", back_populates="tenant")
    down_times = relationship("DownTime", back_populates="tenant")
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
    weekday = Column(Integer, nullable=False)  # 0 = Monday ... 6 = Sunday
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    tenant_shift = relationship("TenantShift", back_populates="timings")

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

    __table_args__ = (
        UniqueConstraint('tenant_id', 'defect_name', name='uix_tenant_defect'),
    )

# ---------------------------> Operation table ends

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

    __table_args__ = (
        UniqueConstraint('tenant_id', 'downtime_name', name='uix_tenant_down_time'),
    )

# ---------------------------> Defect table ends

# <-------------------------- DownTime table starts 
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

    __table_args__ = (
        UniqueConstraint('tenant_id', 'operation_name', name='uix_tenant_operation'),
    )

# ---------------------------> DownTime table ends






