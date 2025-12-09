from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    displayName = models.CharField(max_length=255, blank=True)
    
    # dùng email để login
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    email = models.EmailField(unique=True)