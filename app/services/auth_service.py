from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException
from datetime import datetime

from app.models.models import User, TokenBlacklist
from app.schemas.schemas import UserCreate, LoginRequest
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token


class AuthService:

    @staticmethod
    async def register_user(db: AsyncSession, data: UserCreate) -> User:
        existing = await db.execute(select(User).where(User.email == data.email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")
        user = User(
            name=data.name,
            email=data.email,
            hashed_password=hash_password(data.password),
            role=data.role.value,
            phone=data.phone,
            company=data.company,
        )
        db.add(user)
        await db.flush()
        return user

    @staticmethod
    async def login(db: AsyncSession, data: LoginRequest) -> dict:
        result = await db.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is inactive")

        # Update last login
        await db.execute(
            update(User).where(User.id == user.id).values(last_login=datetime.utcnow())
        )

        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        return {"access_token": access_token, "refresh_token": refresh_token, "user": user}

    @staticmethod
    async def logout(db: AsyncSession, token: str):
        payload = decode_token(token)
        from datetime import timezone
        expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        bl = TokenBlacklist(token=token, expires_at=expires_at)
        db.add(bl)

    @staticmethod
    async def refresh(db: AsyncSession, refresh_token: str) -> str:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Not a refresh token")
        # Check blacklist
        result = await db.execute(
            select(TokenBlacklist).where(TokenBlacklist.token == refresh_token)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=401, detail="Token has been revoked")
        user_id = payload.get("sub")
        return create_access_token({"sub": user_id})

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
