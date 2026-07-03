from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.auth import AuthService
from ...schemas import LoginRequest, TokenResponse

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    result = await service.authenticate(
        username=data.username, password=data.password
    )
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user, token = result
    return TokenResponse(access_token=token)
