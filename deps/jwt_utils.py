from datetime import datetime, timedelta, timezone
from jose import jwt
import os, uuid

ALGORITHM = os.getenv("JWT_ALG","HS256")
SECRET_KEY = os.getenv("JWT_SECRET", "CHANGE_ME_SUPER_SECRET")
ACCESS_TTL   = int(os.getenv("ACCESS_TTL_MIN", "20"))
REFRESH_TTL  = int(os.getenv("REFRESH_TTL_DAYS", "7"))

def _now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())

def _exp_ts(*, minutes: int | None = None, days: int | None = None) -> int:
    now = datetime.now(timezone.utc)
    if minutes is not None:
        return int((now + timedelta(minutes=minutes)).timestamp())
    if days is not None:
        return int((now + timedelta(days=days)).timestamp())
    raise ValueError("Pass minutes or days")

def create_access_token(sub: str, extra: dict | None = None) -> str:
    claims = {
        "sub": sub,
        "type": "access",
        "iat": _now_ts(),
        "exp": _exp_ts(minutes=ACCESS_TTL),
        "jti": str(uuid.uuid4()),
    }
    if extra:
        claims.update(extra)
    return jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(sub: str, extra:dict | None = None) -> str:
    claims = {
        "sub": sub,
        "type": "refresh",
        "iat": _now_ts(),
        "exp": _exp_ts(days=REFRESH_TTL),
        "jti": str(uuid.uuid4()),
    }
    if extra:
        claims.update(extra)
    return jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])