from fastapi.security import OAuth2PasswordBearer
from fastapi import status, Depends, HTTPException, Request

from enum import Enum
from pydantic import BaseModel
from typing import Union
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

SECRET_KEY = "0c985929c3420b61a0cb6d6104995c3f931c40115a53a81f72469e1e4e13a064"  #as signature
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class OpenAPIExtra(str, Enum):
    access_privilege = "access_privilege"

class AccessPrivilege(int, Enum):
    # Lower number means higher privilege
    root = 0
    admin = 1
    general = 2
    default = 99
    
class Token(BaseModel):
    access_token: str
    token_type: str
    
class TokenData(BaseModel):
    username: Union[str, None] = None

class UserInDB(BaseModel):
    username: str
    hash_password: str
    privilege: int

fake_users_db = {
    "general":{
        "username": "general",
        "hash_password": "general",
        "privilege": AccessPrivilege.general.value
    },
    "admin":{
        "username": "admin",
        "hash_password": "admin",
        "privilege": AccessPrivilege.admin.value
    },
    "root":{
        "username": "root",
        "hash_password": "root",
        "privilege": AccessPrivilege.root.value
    }            
}
    
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

def verify_password(plain_password, hashed_password):
    # return pwd_context.verify(plain_password, hashed_password)
    return plain_password == hashed_password

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    
def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hash_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm= ALGORITHM)
    return encoded_jwt
    
def get_current_user(request: Request, OAuth2_token: str = Depends(oauth2_scheme)):
    
    auth_token = None
    
    cookie_token = request.cookies.get("token_in_cookie")
    
    if cookie_token != None:
        # prefer token in cookie
        auth_token = cookie_token.split(" ")[1] # trim "bearer"
        print(f'## Using token_in_cookie')
    else:
        auth_token = OAuth2_token
        print(f'## Using OAuth2 token')
    
    credentials_exception = HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        payload = jwt.decode(auth_token, SECRET_KEY, algorithms=[ALGORITHM]) 
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    
    print(f'## User: {user.username}')
    
    return user

def is_user_general(current_user: UserInDB = Depends(get_current_user)):
    if current_user.privilege != AccessPrivilege.general.value:
        raise HTTPException(status_code=400, detail="Privilege of current user is not general!")
    return current_user

def is_user_admin(current_user: UserInDB = Depends(get_current_user)):
    if current_user.privilege != AccessPrivilege.admin.value:
        raise HTTPException(status_code=400, detail="Privilege of current user is not admin!")
    return current_user

def is_user_root(current_user: UserInDB = Depends(get_current_user)):
    if current_user.privilege != AccessPrivilege.root.value:
        raise HTTPException(status_code=400, detail="Privilege of current user is not root!")
    return current_user