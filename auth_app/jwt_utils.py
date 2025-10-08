"""Small JWT helper for access/refresh tokens using PyJWT"""
import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings
import hashlib


def _now_utc() -> datetime:
    """Current UTC time with timezone info"""  
    return datetime.now(tz=timezone.utc)


def _exp_ts(delta: timedelta) -> int:
    """Calculate expiration timestamp (int) from now + delta"""
    return int((_now_utc() + delta).timestamp())


def _hash(token: str) -> str:
    """Hash a token string with SHA-256 and return hex digest"""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def _is_refresh_token_blacklisted(token: str) -> bool:
    """Check if a refresh token is blacklisted (only if blacklist enabled)"""
    from auth_app.models import BlacklistedToken
    return BlacklistedToken.objects.filter(token_hash=_hash(token)).exists()


def create_access_token(user) -> str:
    """Create a signed JWT access token for the given user"""
    mins = int(getattr(settings, 'ACCESS_TOKEN_LIFETIME_MINUTES', 15))
    payload = {
        'sub': str(user.id),
        'email': user.email,
        'type': 'access',
        'iat': int(_now_utc().timestamp()),
        'exp': _exp_ts(timedelta(minutes=mins)),
    }
    alg = getattr(settings, 'JWT_ALGORITHM', 'HS256')
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=alg)


def create_refresh_token(user) -> str:
    """Create a signed JWT refresh token for the given user"""
    days = int(getattr(settings, 'REFRESH_TOKEN_LIFETIME_DAYS', 7))
    payload = {
        'sub': str(user.id),
        'type': 'refresh',
        'iat': int(_now_utc().timestamp()),
        'exp': _exp_ts(timedelta(days=days)),
    }
    alg = getattr(settings, 'JWT_ALGORITHM', 'HS256')
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=alg)


def decode_token(token: str, expected_type: str | None = None) -> dict:
    """Decode and verify a JWT, optionally enforcing the token type ('access' or 'refresh')"""
    alg = getattr(settings, 'JWT_ALGORITHM', 'HS256')
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[alg])
    if expected_type and payload.get('type') != expected_type:
        raise jwt.InvalidTokenError('Unexpected token type')
    if expected_type == 'refresh' and getattr(settings, 'JWT_BLACKLIST_ENABLED', True):
        if _is_refresh_token_blacklisted(token):
            raise jwt.InvalidTokenError('Token blacklisted')
    return payload