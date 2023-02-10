from fastapi import APIRouter, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from datetime import timedelta

# modules in current folder
import auth

router = APIRouter()

@router.post("/token", 
    response_model=auth.Token, 
    tags=["login"],
    include_in_schema=False
)
def get_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = auth.authenticate_user(auth.fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
            )
        
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/fake-user", 
    tags=["login"],
    openapi_extra={auth.OpenAPIExtra.access_privilege.value: auth.AccessPrivilege.default}
)
def to_make_authorize_button_show_up(current_user: auth.UserInDB = Depends(auth.is_user_general)):
    return "ok"

@router.get("/general-test", 
    tags=["general"],
    openapi_extra={auth.OpenAPIExtra.access_privilege.value: auth.AccessPrivilege.general}
)
def test(current_user: auth.UserInDB = Depends(auth.is_user_general)):
    return "ok"

@router.get("/admin-test", 
    tags=["admin"],
    openapi_extra={auth.OpenAPIExtra.access_privilege.value: auth.AccessPrivilege.admin}
)
def test(current_user: auth.UserInDB = Depends(auth.is_user_admin)):
    return "ok"

@router.get("/root-test", 
    tags=["root"],
    openapi_extra={auth.OpenAPIExtra.access_privilege.value: auth.AccessPrivilege.root}
)
def test(current_user: auth.UserInDB = Depends(auth.is_user_root)):
    return "ok"

@router.get("/no-privilege-test")
def test(current_user: auth.UserInDB = Depends(auth.is_user_root)):
    return "ok"