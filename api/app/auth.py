"""Organizer accounts: sign up, sign in, and who-am-I.

With DATABASE_URL set, accounts live in PostgreSQL and passwords are stored only as Argon2 hashes.
Without it the API stays in mock mode: any login works and nobody is checked,
so designers can build screens without installing a database.
"""
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import jwt
import psycopg
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from . import db
from .schemas import LoginRequest, Me, OrganizerSignup, Token

log = logging.getLogger("eventreach.auth")
router = APIRouter(tags=["Auth"])

TOKEN_HOURS = 8
MOCK_ME = Me(id="org_001", name="Demo Organizer", email="organizer@example.com", role="organizer")

_hasher = PasswordHasher()
_DUMMY_HASH = _hasher.hash("not-a-real-password")  # lets unknown emails take as long as wrong passwords
_temporary_key = secrets.token_urlsafe(48)
_warned = False
_bearer = HTTPBearer(auto_error=False, description="Paste the token from /auth/login")


# ---------- passwords and tokens ----------

def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(stored_hash: str, plain: str) -> bool:
    try:
        return _hasher.verify(stored_hash, plain)
    except (VerificationError, InvalidHashError):
        return False


def _secret() -> str:
    """SECRET_KEY from .env when it is long enough, otherwise a temporary key for this run."""
    global _warned
    key = os.getenv("SECRET_KEY", "")
    if len(key) >= 32:
        return key
    if not _warned:
        log.warning("SECRET_KEY is missing or shorter than 32 characters. Using a temporary key, "
                    "so everyone is signed out when the server restarts.")
        _warned = True
    return _temporary_key


def create_token(organizer_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    claims = {"sub": organizer_id, "role": role, "iat": now, "exp": now + timedelta(hours=TOKEN_HOURS)}
    return jwt.encode(claims, _secret(), algorithm="HS256")


# ---------- accounts ----------

def create_organizer(conn: psycopg.Connection, name: str, email: str, password: str, role: str = "organizer") -> dict:
    """Insert an account and commit. Raises psycopg.errors.UniqueViolation if the email is taken."""
    row = conn.execute(
        "INSERT INTO organizers (email, name, role, password_hash) VALUES (%s, %s, %s, %s) "
        "RETURNING id, name, email, role",
        (email.strip().lower(), name.strip(), role, hash_password(password)),
    ).fetchone()
    conn.commit()
    return row


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(401, message, headers={"WWW-Authenticate": "Bearer"})


def current_organizer(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    conn: Optional[psycopg.Connection] = Depends(db.get_conn),
) -> Me:
    """Use as a dependency on any route that needs a signed-in organizer."""
    if conn is None:
        return MOCK_ME
    if creds is None:
        raise _unauthorized("Sign in first.")
    try:
        claims = jwt.decode(creds.credentials, _secret(), algorithms=["HS256"])
        organizer_id = UUID(claims["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise _unauthorized("Your session is not valid or has expired. Sign in again.") from None
    row = conn.execute("SELECT id, name, email, role FROM organizers WHERE id = %s", (organizer_id,)).fetchone()
    if row is None:
        raise _unauthorized("This account no longer exists.")
    return Me(id=str(row["id"]), name=row["name"], email=row["email"], role=row["role"])


def require_admin(me: Me = Depends(current_organizer)) -> Me:
    if me.role != "admin":
        raise HTTPException(403, "Only an admin can do this.")
    return me


# ---------- routes ----------

@router.post("/auth/register", response_model=Token, status_code=201)
def register(body: OrganizerSignup, conn: Optional[psycopg.Connection] = Depends(db.get_conn)) -> Token:
    """Create an organizer account and sign in. Set ALLOW_REGISTRATION=false to close sign-up."""
    if conn is None:
        return Token(access_token="mock-token")
    if os.getenv("ALLOW_REGISTRATION", "true").strip().lower() != "true":
        raise HTTPException(403, "Sign-up is closed. Ask an admin to create your account.")
    try:
        row = create_organizer(conn, body.name, body.email, body.password)
    except psycopg.errors.UniqueViolation:
        conn.rollback()
        raise HTTPException(409, "An account with this email already exists.") from None
    return Token(access_token=create_token(str(row["id"]), row["role"]))


@router.post("/auth/login", response_model=Token)
def login(body: LoginRequest, conn: Optional[psycopg.Connection] = Depends(db.get_conn)) -> Token:
    if conn is None:
        return Token(access_token="mock-token")
    row = conn.execute(
        "SELECT id, role, password_hash FROM organizers WHERE email = %s", (body.email.strip().lower(),)
    ).fetchone()
    password_ok = verify_password(row["password_hash"] if row else _DUMMY_HASH, body.password)
    if row is None or not password_ok:
        raise _unauthorized("Email or password is incorrect.")  # same message for both, on purpose
    return Token(access_token=create_token(str(row["id"]), row["role"]))


@router.get("/me", response_model=Me)
def me(who: Me = Depends(current_organizer)) -> Me:
    return who
