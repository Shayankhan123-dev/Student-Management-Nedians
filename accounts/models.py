from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model extending Django's built-in AbstractUser.
    We add a 'role' field to distinguish admins from students.
    """
    ROLE_ADMIN = 'admin'
    ROLE_STUDENT = 'student'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_STUDENT, 'Student'),
    ]

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=ROLE_STUDENT
    )

    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    def is_student(self):
        return self.role == self.ROLE_STUDENT

    def __str__(self):
        return f"{self.username} ({self.role})"