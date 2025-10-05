from os import access
from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..import database, schemas, models,utls, oauth2
from sqlalchemy.exc import SQLAlchemyError



router = APIRouter(tags=['Authentication'])

@router.post('/login',response_model= schemas.Token)
def login(user_credentials:OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    # print(user_credentials.username)
    # print(user_credentials.password)
    try:
        type = utls.check_type(user_credentials.username)
        if type == 'email':
            user = db.query(models.User).filter(models.User.email == user_credentials.username.lower()).first()
        elif type == 'upi':

            user = db.query(models.User).filter(models.User.employee_id == user_credentials.username.lower()).first()
           
        else:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"{user_credentials.username} is not valid username, please re-check !!!")
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f" {user_credentials.username} no such username Found")
        role = db.query(models.UserRole).filter(models.UserRole.id == user.role_id).first()

        tenant_details = db.query(models.Tenant).filter(models.Tenant.id == user.tenant_id).first()
        # print(tenant_details.tenant_name)
        if not tenant_details:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"No such tenant found")
        # print(tenant_details.is_active) # for debugginh purpose 
        if not tenant_details.is_verified:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail= f"Tenant {tenant_details.tenant_name} is not varified, Please contact your Admin")
        if not tenant_details.is_active :
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail= f"Tenant {tenant_details.tenant_name} is not active, Please contact your Admin")
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail= "Invalid credentials")
        
        if not utls.verify(user_credentials.password, user.password):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail= "Invalid credentials")

        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail= f"{user.employee_id} with user name {user.user_name} is not varified, Please contact your Admin") # f"{user.user_name} user not varifed ")
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail= f"{user.employee_id} with user name {user.user_name} is not active, Please contact your Admin") 
        
    
            
        # print(f"================{user.is_verified_user}")
        
        # CREATE TOKEN 
        access_token= oauth2.create_access_token(data= {"user_id": user.id})
        # print(f"User {user} logged in successfully")
        # print(access_token)
        # print(role.user_role)
        return {"access_token":access_token, "token_type":"bearer", "role_id": user.role_id} 
    except HTTPException as he:
        raise he
    except SQLAlchemyError as e:
    
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Intenal Sever Error {str(e)}")     
    