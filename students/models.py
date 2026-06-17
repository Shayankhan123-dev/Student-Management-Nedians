from django.db import models
from accounts.models import User


class Class(models.Model):
    """
    Represents a class/grade in the school.
    e.g. Class 9, Class 10 (AKG Board)
    """
    BOARD_REGULAR = 'Regular'
    BOARD_AKG = 'AKG'

    BOARD_CHOICES = [
        (BOARD_REGULAR, 'Regular'),
        (BOARD_AKG, 'AKG Board'),
    ]

    name = models.CharField(max_length=50)
    board = models.CharField(
        max_length=10,
        choices=BOARD_CHOICES,
        default=BOARD_REGULAR
    )

    class Meta:
        verbose_name_plural = 'Classes'
        unique_together = ['name', 'board']

    def __str__(self):
        if self.board == self.BOARD_AKG:
            return f"{self.name} (AKG Board)"
        return self.name


class Student(models.Model):
    """
    Student profile linked to a User account.
    Only users with role='student' will have this profile.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    student_class = models.ForeignKey(
        Class,
        on_delete=models.PROTECT,
        related_name='students'
    )
    student_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15, blank=True)
    is_frozen = models.BooleanField(default=False)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.student_id})"