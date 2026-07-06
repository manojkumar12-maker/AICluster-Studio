from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.auth import AuthService
from ...schemas import LoginRequest, TokenResponse, UserResponse
from ...middleware import limiter

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=TokenResponse)
@limiter.limit("100/minute")
async def login(request: Request, data: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    result = await service.authenticate(
        username=data.username, password=data.password
    )
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user, token = result
    user_info = UserResponse(
        id=user.id,
        username=user.username,
        email=getattr(user, "email", ""),
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )
    return TokenResponse(access_token=token, user=user_info)
