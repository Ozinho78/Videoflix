from django.db import models  # ORM base classes
from django.contrib.auth.models import User  # Link blacklisted entries to a user

class BlacklistedToken(models.Model):
    """
    Stores a hashed refresh token that has been invalidated (user logged out).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='blacklisted_tokens')  # Optional link to user
    token_hash = models.CharField(max_length=64, unique=True)  # SHA-256 hex digest of the refresh token
    created_at = models.DateTimeField(auto_now_add=True)  # When it was blacklisted

    def __str__(self):
        # Helpful display in admin/debug
        return f'BlacklistedToken(user={self.user_id}, created_at={self.created_at})'