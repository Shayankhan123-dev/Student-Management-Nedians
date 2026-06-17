from django.db import models
from students.models import Student, Class


class Subject(models.Model):
    """
    A subject taught in a specific class.
    e.g. Mathematics in Class 9
    """
    student_class = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='subjects'
    )
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ['student_class', 'name']

    def __str__(self):
        return f"{self.name} - {self.student_class}"


class Test(models.Model):
    """
    An exam or test event for a class.
    e.g. Unit Test 1, Mid-Term Exam
    """
    student_class = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='tests'
    )
    name = models.CharField(max_length=150)
    date = models.DateField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.student_class}"


class Mark(models.Model):
    """
    Individual marks for one student in one subject for one test.
    """
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name='marks'
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='marks'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='marks'
    )
    obtained_marks = models.PositiveIntegerField()
    total_marks = models.PositiveIntegerField()

    class Meta:
        unique_together = ['test', 'student', 'subject']

    @property
    def percentage(self):
        if self.total_marks == 0:
            return 0
        return round((self.obtained_marks / self.total_marks) * 100, 2)

    def __str__(self):
        return f"{self.student.full_name} - {self.subject.name} - {self.test.name}"