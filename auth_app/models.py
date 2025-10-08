from django.db import models
from django.contrib.auth.models import User

class BlacklistedToken(models.Model):
    """Stores a hashed refresh token that has been invalidated (user logged out)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='blacklisted_tokens')
    token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """String representation showing user and creation time""" 
        return f'BlacklistedToken(user={self.user_id}, created_at={self.created_at})'