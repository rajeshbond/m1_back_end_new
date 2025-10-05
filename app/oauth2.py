
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app import models, schemas , database
from sqlalchemy.orm import Session
from .config import settings
import pytz

oauth2_scheme = OAuth2PasswordBearer(tokenUrl= 'login')

india_tz = pytz.timezone('Asia/Kolkata')

# SECRET_KEY
#Algorithm 
# expriation time 

# SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 120
# ================================================================
# #  This below code are with env varliable settings
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


def create_access_token(data: dict):
    to_encode = data.copy()
    # print(to_encode)
    expire = datetime.now(india_tz) + timedelta(minutes= ACCESS_TOKEN_EXPIRE_MINUTES)
    # to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
   
    return encoded_jwt




def verify_access_token(token: str, credentials_exception):
    
    try:
    
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        id: str = payload.get("user_id")
        
        if id is None:
            raise credentials_exception
        
        token_data = schemas.TokenData(id = str(id))
    
    except JWTError:
        raise credentials_exception
    return token_data

def get_current_user(token: str = Depends(oauth2_scheme ),db:Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},)
    
    token = verify_access_token(token, credentials_exception)
    user = db.query(models.User).filter(models.User.id ==  token.id).first()
    # print(user)
    
    return user
    
    # return verify_access_token(token, credentials_exception)
    
                        