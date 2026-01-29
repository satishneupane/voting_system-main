from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import UserProfile

# Create profile automatically
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

# Email on login
@receiver(user_logged_in)
def login_alert(sender, request, user, **kwargs):
    send_mail(
        "Login Alert",
        "You just logged into the voting system.",
        "noreply@voting.com",
        [user.email],
        fail_silently=True,
    )
