from passlib.context import CryptContext
import re



pwd_context = CryptContext(schemes=["bcrypt"], deprecated = "auto")

def hash(password:str):
    return pwd_context.hash(password)

def verify(plain_password,hashed_passwprd):
    return pwd_context.verify(plain_password, hashed_passwprd)

def employee_code(employee_id,tenant_code):
    new_employe_code = f"{employee_id}@{tenant_code}"
    return new_employe_code.lower()




def check_type(value: str) -> str:
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    upi_pattern = r'^[\w\.-]+@[\w\.-]+$'
    
    if re.match(email_pattern, value):
        return "email"
    elif re.match(upi_pattern, value):
        return "upi"
    else:
        return "invalid"
    
def dividecode(value:str) -> str:
    if re.match(r"^\d+@\w+$", value):
        return value.split("@")[1]
    else:
        return None