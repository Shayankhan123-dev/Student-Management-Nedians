from django.db import models
from students.models import Student, Class


class Attendance(models.Model):
    """
    One record per student per day.
    """
    STATUS_PRESENT = 'PRESENT'
    STATUS_ABSENT = 'ABSENT'

    STATUS_CHOICES = [
        (STATUS_PRESENT, 'Present'),
        (STATUS_ABSENT, 'Absent'),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    student_class = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    date = models.DateField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PRESENT
    )
    marked_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'date']

    def __str__(self):
        return f"{self.student.full_name} - {self.date} - {self.status}"