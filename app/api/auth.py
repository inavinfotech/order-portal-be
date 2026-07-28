from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from app.auth.deps import verify_dashboard_auth
from app.auth.security import create_access_token
import os

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    status: str
    email: str
    access_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    expected_email = os.getenv("DASHBOARD_EMAIL", "")
    expected_pass = os.getenv("DASHBOARD_PASSWORD", "")
    
    if request.email != expected_email or request.password != expected_pass:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Email or Password"
        )
    
    # Generate JWT token
    access_token = create_access_token(data={"sub": expected_email, "role": "admin"})
    
    return {
        "status": "success",
        "email": expected_email,
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/verify")
def verify(auth: bool = Depends(verify_dashboard_auth)):
    return {"status": "authenticated"}
