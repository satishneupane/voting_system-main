from django.conf import settings
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,   # ✅ THIS is the fix
        on_delete=models.CASCADE
    )
    voter_id = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return f"{self.user.username} - {self.voter_id}"

