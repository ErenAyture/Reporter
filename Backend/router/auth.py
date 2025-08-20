# router/auth.py
from datetime import datetime, timezone
import jwt  # PyJWT
from fastapi import HTTPException
from config import settings

def decode_dashboard_jwt(token: str) -> tuple[str, int | None]:
    """Return (username, exp_epoch_seconds) or raise 401 on error."""
    opts = {"verify_aud": False}
    try:
        if settings.DASHBOARD_JWT_ALG.upper() == "RS256":
            if not settings.DASHBOARD_JWT_PUBLIC_KEY:
                raise RuntimeError("DASHBOARD_JWT_PUBLIC_KEY missing for RS256")
            payload = jwt.decode(
                token, settings.DASHBOARD_JWT_PUBLIC_KEY,
                algorithms=["RS256"], options=opts
            )
        else:
            payload = jwt.decode(
                token, settings.DASHBOARD_JWT_SECRET,
                algorithms=["HS256"], options=opts
            )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = (payload.get("username")
                or payload.get("preferred_username")
                or payload.get("email")
                or payload.get("sub"))
    if not username:
        raise HTTPException(status_code=401, detail="Username not found in token")

    return username, payload.get("exp")
