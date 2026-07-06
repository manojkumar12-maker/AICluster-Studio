from datetime import timedelta, datetime, timezone
import os
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt, JWTError
from passlib.context import CryptContext

from ..models.user import User
from ..config import settings
from ..database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_scheme = HTTPBearer(auto_error=False)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate(self, username: str, password: str) -> tuple[User, str] | None:
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        if not user or not pwd_context.verify(password, user.hashed_password):
            return None
        if not user.is_active:
            return None

        token = jwt.encode(
            {
                "sub": user.id,
                "role": user.role,
                "exp": datetime.now(timezone.utc) + timedelta(
                    minutes=settings.access_token_expire_minutes
                ),
            },
            settings.secret_key,
            algorithm=settings.algorithm,
        )
        return user, token

    async def seed_default_admin(self) -> str | None:
        result = await self.db.execute(
            select(User).where(User.username == "admin")
        )
        if result.scalar_one_or_none():
            return None

        password = os.environ.get("AICLUSTER_ADMIN_PASSWORD") or "admin"
        admin = User(
            username="admin",
            hashed_password=pwd_context.hash(password),
            role="admin",
        )
        self.db.add(admin)
        await self.db.commit()
        return password

    async def get_user_by_id(self, user_id: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user
