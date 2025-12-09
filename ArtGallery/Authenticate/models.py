from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class User(AbstractUser):
    displayName = models.CharField(max_length=255, blank=True)
    
    # dùng email để login
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    email = models.EmailField(unique=True)

class Painting(models.Model):
    VISIBILITY_CHOICES = [
        ('private', 'Private'),
        ('public', 'Public'),
        ('unlisted', 'Unlisted'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='paintings')
    frame_number = models.IntegerField()  # Số thứ tự khung (1, 2, 3, ...)
    title = models.CharField(max_length=255, default='Untitled')
    description = models.TextField(blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    thumbnail_url = models.URLField(max_length=500, blank=True, null=True)
    cloudinary_public_id = models.CharField(max_length=500, blank=True, null=True)
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='private')
    tags = models.JSONField(default=list, blank=True)
    has_image = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.owner.username} - Frame {self.frame_number}"

    class Meta:
        ordering = ['frame_number']
        unique_together = ['owner', 'frame_number']  # Mỗi user không có 2 frame cùng số