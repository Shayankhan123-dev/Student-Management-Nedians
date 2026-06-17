from django.contrib import admin
from .models import Subject, Test, Mark


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'student_class']


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ['name', 'student_class', 'date']


@admin.register(Mark)
class MarkAdmin(admin.ModelAdmin):
    list_display = ['student', 'test', 'subject', 'obtained_marks', 'total_marks']