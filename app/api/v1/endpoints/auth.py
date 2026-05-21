from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.schemas import LoginRequest, LoginResponse, UserCreate, UserOut, RefreshTokenRequest, APIResponse
from app.services.auth_service import AuthService
from app.core.security import get_current_user, bearer_scheme
from app.utils.audit import log_action

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=APIResponse, summary="Register new user")
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await AuthService.register_user(db, data)
    return APIResponse.ok(
        data=UserOut.model_validate(user),
        message="User registered successfully"
    )


@router.post("/login", response_model=APIResponse, summary="Login and get JWT tokens")
async def login(data: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    result = await AuthService.login(db, data)
    await log_action(
        db, action="LOGIN", user_id=result["user"].id,
        entity_type="User", entity_id=str(result["user"].id),
        description=f"User {result['user'].email} logged in",
        ip_address=request.client.host
    )
    return APIResponse.ok(
        data=LoginResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            user=result["user"],
        ),
        message="Login successful"
    )


@router.post("/logout", response_model=APIResponse, summary="Logout and blacklist token")
async def logout(
    credentials=Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    await AuthService.logout(db, credentials.credentials)
    await log_action(db, action="LOGOUT", user_id=current_user.id, entity_type="User")
    return APIResponse.ok(message="Logged out successfully")


@router.post("/refresh", response_model=APIResponse, summary="Get new access token")
async def refresh_token(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    new_token = await AuthService.refresh(db, data.refresh_token)
    return APIResponse.ok(data={"access_token": new_token, "token_type": "bearer"})


@router.get("/me", response_model=APIResponse, summary="Get current logged-in user")
async def get_me(current_user=Depends(get_current_user)):
    return APIResponse.ok(data=UserOut.model_validate(current_user))
