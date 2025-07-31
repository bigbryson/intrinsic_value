# /apps/connection_page/models.py
from django.db import models
from django.conf import settings

class SchwabToken(models.Model):
    # This creates a one-to-one link to a user.
    # Each user can only have one Schwab token.
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    access_token = models.TextField(null=True, blank=True)
    refresh_token = models.TextField(null=True, blank=True)
    expires_in = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Schwab Token for {self.user.username}"
