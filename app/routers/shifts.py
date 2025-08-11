from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta, time
from app import schemas, models, oauth2
from ..database import get_db
import pandas as pd
from ..function import shifts_fn

router = APIRouter(prefix="/shifts/v1", tags=["Shifts"])


