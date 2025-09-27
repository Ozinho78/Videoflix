"""
Small JWT helper for access/refresh tokens using PyJWT.
"""
import jwt  # PyJWT for encoding/decoding
from datetime import datetime, timedelta, timezone  # For UTC timestamps
from django.conf import settings  # To read SECRET_KEY and lifetimes
import hashlib  # To hash tokens for blacklist checks


def _now_utc() -> datetime:
    # Return a timezone-aware "now" in UTC
    return datetime.now(tz=timezone.utc)


def _exp_ts(delta: timedelta) -> int:
    # Build a UNIX timestamp (seconds) for exp claim
    return int((_now_utc() + delta).timestamp())


def _hash(token: str) -> str:
    # Stable SHA-256 hex digest used to store/lookup blacklisted tokens
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def _is_refresh_token_blacklisted(token: str) -> bool:
    # Query the DB to see if we blacklisted this token before
    from auth_app.models import BlacklistedToken  # Local import to avoid early app loading
    return BlacklistedToken.objects.filter(token_hash=_hash(token)).exists()


def create_access_token(user) -> str:
    # Lifetime (minutes) from settings or default 15
    mins = int(getattr(settings, 'ACCESS_TOKEN_LIFETIME_MINUTES', 15))
    # Minimal payload with standard claims
    payload = {
        'sub': str(user.id),        # Subject = user id
        'email': user.email,        # Useful claim for FE debugging
        'type': 'access',           # Distinguish token type
        'iat': int(_now_utc().timestamp()),        # Issued at
        'exp': _exp_ts(timedelta(minutes=mins)),   # Expiration
    }
    # Sign with project SECRET_KEY and algorithm from settings or HS256
    alg = getattr(settings, 'JWT_ALGORITHM', 'HS256')
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=alg)


def create_refresh_token(user) -> str:
    # Lifetime (days) from settings or default 7
    days = int(getattr(settings, 'REFRESH_TOKEN_LIFETIME_DAYS', 7))
    payload = {
        'sub': str(user.id),        # Subject = user id
        'type': 'refresh',          # Refresh token type
        'iat': int(_now_utc().timestamp()),
        'exp': _exp_ts(timedelta(days=days)),
    }
    alg = getattr(settings, 'JWT_ALGORITHM', 'HS256')
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=alg)


def decode_token(token: str, expected_type: str | None = None) -> dict:
    # Decode and verify signature/exp; raise jwt exceptions on failure
    alg = getattr(settings, 'JWT_ALGORITHM', 'HS256')
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[alg])

    # Enforce token type if requested
    if expected_type and payload.get('type') != expected_type:
        raise jwt.InvalidTokenError('Unexpected token type')

    # Extra: reject refresh tokens that were blacklisted on logout
    if expected_type == 'refresh' and getattr(settings, 'JWT_BLACKLIST_ENABLED', True):
        if _is_refresh_token_blacklisted(token):
            raise jwt.InvalidTokenError('Token blacklisted')

    return payload
