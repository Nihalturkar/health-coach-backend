from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from app.config import settings
import hashlib
import secrets


def _parse_duration(duration_str: str) -> timedelta:
    """Parse duration string like '15m', '7d', '1h' into timedelta."""
    unit = duration_str[-1]
    value = int(duration_str[:-1])
    if unit == "m":
        return timedelta(minutes=value)
    elif unit == "h":
        return timedelta(hours=value)
    elif unit == "d":
        return timedelta(days=value)
    raise ValueError(f"Unknown duration unit: {unit}")


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + _parse_duration(settings.JWT_EXPIRE)
    payload = {"sub": user_id, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def create_refresh_token() -> tuple[str, str]:
    """Returns (raw_token, hashed_token). Store hash in DB, send raw to client."""
    raw = secrets.token_urlsafe(64)
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def decode_access_token(token: str) -> str | None:
    """Returns user_id string or None if invalid."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        if payload.get("type") != "access":
            return None
        return payload.get("sub")
    except JWTError:
        return None


def get_refresh_token_expiry() -> datetime:
    return datetime.now(timezone.utc) + _parse_duration(settings.JWT_REFRESH_EXPIRE)
