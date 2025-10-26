from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    Custom user model that inherits from Django's AbstractUser.
    This provides all the necessary fields and methods for authentication.
    """
    pass