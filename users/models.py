from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import os


def profile_picture_upload_path(instance, filename):
    """
    Generate upload path for profile pictures using username.
    Format: profile_pictures/username.ext
    """
    # Get file extension
    ext = filename.split('.')[-1] if '.' in filename else ''

    # Create filename with username
    if ext:
        filename = f"{instance.user.username}.{ext}"
    else:
        filename = instance.user.username

    # Return full path
    return os.path.join('profile_pictures', filename)


class UserProfile(models.Model):
    """
    Extension of Django's built-in User model.
    Stores role and additional user metadata.
    """
    
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        BETA_USER = 'beta_user', 'Beta User'
        VIEWER = 'viewer', 'Viewer'
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER
    )
    profile_picture = models.ImageField(
        upload_to=profile_picture_upload_path,
        blank=True,
        null=True,
        help_text='Profile picture (max 5MB, recommended: 400x400px)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.username} ({self.role})"
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    @property
    def is_beta_user(self):
        return self.role in [self.Role.ADMIN, self.Role.BETA_USER]


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile when a new User is created."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile when the User is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
