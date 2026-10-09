"""Single-user cookie-session auth using only the standard library.

Env vars:
  AUTH_USERNAME        login name (required)
  AUTH_PASSWORD_HASH   "pbkdf2_sha256$iterations$salt_b64$hash_b64" (see hash_password.py)
  AUTH_PASSWORD        plain-text fallback (discouraged)
  SESSION_SECRET       HMAC key for session cookies (required, >= 16 chars)
  SESSION_TTL_SECONDS  session lifetime (default 7 days)
  COOKIE_SECURE        "1" to set the Secure flag (use when served over HTTPS)
"""
import base64
import hashlib
import hmac
import logging
import os
import secrets
import time
from collections import defaultdict, deque
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

logger = logging.getLogger("auth")

COOKIE_NAME = "session"
PBKDF2_ITERATIONS = 600_000

router = APIRouter(prefix="/api/auth", tags=["auth"])


def hash_password(password: str, iterations: int = PBKDF2_ITERATIONS) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return "pbkdf2_sha256${}${}${}".format(
        iterations, base64.b64encode(salt).decode(), base64.b64encode(dk).decode()
    )


def _verify_hash(password: str, stored: str) -> bool:
    try:
        algo, iters, salt_b64, dk_b64 = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), base64.b64decode(salt_b64), int(iters)
        )
        return hmac.compare_digest(dk, base64.b64decode(dk_b64))
    except Exception:
        return False


def _env(name: str) -> str:
    """Read an env var, tolerating quotes left in by docker-compose v1 env_file parsing."""
    v = os.environ.get(name, "").strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
        v = v[1:-1]
    return v


def _config():
    return (_env("AUTH_USERNAME"), _env("AUTH_PASSWORD_HASH"),
            os.environ.get("AUTH_PASSWORD", ""), _env("SESSION_SECRET"))


def auth_configured() -> bool:
    username, pw_hash, pw_plain, secret = _config()
    return bool(username and (pw_hash or pw_plain) and len(secret) >= 16)


def warn_if_unconfigured() -> None:
    if not auth_configured():
        logger.warning(
            "AUTH NOT CONFIGURED: set AUTH_USERNAME, AUTH_PASSWORD_HASH (or AUTH_PASSWORD) and "
            "SESSION_SECRET (>=16 chars). All protected endpoints will return 503."
        )
    elif not _env("AUTH_PASSWORD_HASH"):
        logger.warning("Using plain AUTH_PASSWORD; prefer AUTH_PASSWORD_HASH (backend/hash_password.py).")


def _ttl() -> int:
    try:
        return int(os.environ.get("SESSION_TTL_SECONDS", 7 * 24 * 3600))
    except ValueError:
        return 7 * 24 * 3600


def _sign(payload: str) -> str:
    key = _env("SESSION_SECRET").encode()
    return hmac.new(key, payload.encode(), hashlib.sha256).hexdigest()


def make_token(username: str) -> str:
    exp = int(time.time()) + _ttl()
    user_b64 = base64.urlsafe_b64encode(username.encode()).decode().rstrip("=")
    payload = f"{user_b64}.{exp}"
    return f"{payload}.{_sign(payload)}"


def read_token(token: Optional[str]) -> Optional[str]:
    """Return username if token is valid and unexpired, else None."""
    if not token:
        return None
    try:
        user_b64, exp, sig = token.split(".")
        if not hmac.compare_digest(sig, _sign(f"{user_b64}.{exp}")):
            return None
        if int(exp) < time.time():
            return None
        username = base64.urlsafe_b64decode(user_b64 + "=" * (-len(user_b64) % 4)).decode()
    except Exception:
        return None
    expected = _env("AUTH_USERNAME")
    if not hmac.compare_digest(username.encode(), expected.encode()):
        return None
    return username


def require_auth(request: Request) -> str:
    if not auth_configured():
        raise HTTPException(status_code=503, detail="auth not configured")
    user = read_token(request.cookies.get(COOKIE_NAME))
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


# ── Rate limiting (in-memory, per client IP) ─────────────────────────────────
MAX_FAILURES = 5
WINDOW_SECONDS = 300
_failures: dict = defaultdict(deque)


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-real-ip")
    if fwd:
        return fwd
    return request.client.host if request.client else "unknown"


def _blocked(ip: str) -> bool:
    q = _failures[ip]
    now = time.time()
    while q and q[0] < now - WINDOW_SECONDS:
        q.popleft()
    return len(q) >= MAX_FAILURES


class LoginBody(BaseModel):
    username: str
    password: str


def _check_credentials(username: str, password: str) -> bool:
    exp_user, pw_hash, pw_plain, _ = _config()
    user_ok = hmac.compare_digest(username.encode(), exp_user.encode())
    if pw_hash:
        pw_ok = _verify_hash(password, pw_hash)
    else:
        pw_ok = hmac.compare_digest(password.encode(), pw_plain.encode())
    return user_ok and pw_ok


@router.post("/login")
def login(body: LoginBody, request: Request, response: Response):
    if not auth_configured():
        raise HTTPException(status_code=503, detail="auth not configured")
    ip = _client_ip(request)
    if _blocked(ip):
        raise HTTPException(status_code=429, detail="Too many failed attempts; try again later")
    if not _check_credentials(body.username, body.password):
        _failures[ip].append(time.time())
        logger.warning("Failed login from %s", ip)
        raise HTTPException(status_code=401, detail="Invalid username or password")
    _failures.pop(ip, None)
    response.set_cookie(
        COOKIE_NAME,
        make_token(body.username),
        max_age=_ttl(),
        httponly=True,
        samesite="lax",
        secure=os.environ.get("COOKIE_SECURE", "0") == "1",
        path="/",
    )
    return {"username": body.username}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/me")
def me(user: str = Depends(require_auth)):
    return {"username": user}
