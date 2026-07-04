import re

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from app.config import settings
from app.database import get_db
from app.services.auth import AuthService
from app.models.user import User

security_scheme = HTTPBearer(auto_error=False)

PUBLIC_PATHS = {
    "/api/v1/health",
    "/api/v1/auth/login",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/",
}

PUBLIC_PREFIXES = {
    "/static/",
    "/openapi/",
}


def is_public_path(path: str) -> bool:
    if path in PUBLIC_PATHS:
        return True
    for prefix in PUBLIC_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


WORKER_ROUTE_PATTERNS = [
    re.compile(r"^/api/v1/workers/register$"),
    re.compile(r"^/api/v1/workers/heartbeat$"),
    re.compile(r"^/api/v1/workers/[^/]+/next-job$"),
    re.compile(r"^/api/v1/workers/[^/]+/progress$"),
    re.compile(r"^/api/v1/workers/[^/]+/result$"),
]


def is_worker_route(path: str) -> bool:
    for pattern in WORKER_ROUTE_PATTERNS:
        if pattern.match(path):
            return True
    return False


async def auth_middleware(request: Request, call_next):
    path = request.url.path
    if is_public_path(path):
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return Response(
            content='{"detail":"Not authenticated"}',
            status_code=status.HTTP_401_UNAUTHORIZED,
            media_type="application/json",
        )

    token = auth_header.split(" ", 1)[1]

    # Worker routes accept JWT or worker_secret
    if is_worker_route(path):
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm],
            )
            request.state.user_id = payload.get("sub")
            request.state.user_role = payload.get("role")
            return await call_next(request)
        except JWTError:
            if token == settings.secret_key:
                request.state.user_id = "worker"
                request.state.user_role = "worker"
                return await call_next(request)
        return Response(
            content='{"detail":"Invalid worker authentication"}',
            status_code=status.HTTP_401_UNAUTHORIZED,
            media_type="application/json",
        )

    # All other routes use JWT
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        request.state.user_id = payload.get("sub")
        request.state.user_role = payload.get("role")
    except JWTError:
        return Response(
            content='{"detail":"Invalid token"}',
            status_code=status.HTTP_401_UNAUTHORIZED,
            media_type="application/json",
        )

    return await call_next(request)


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


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user


async def verify_worker_token(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> str | None:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Worker authentication required",
        )
    token = credentials.credentials
    # For v1.3.1, worker secret is validated against the master's secret key
    # In future versions, this will use a configurable list of worker secrets
    if token != settings.secret_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid worker secret",
        )
    return token


def admin_required():
    return Depends(require_admin)


def auth_required():
    return Depends(get_current_user)
