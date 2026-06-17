from django.contrib import admin
from .models import Class, Student


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'board']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'student_id', 'student_class', 'is_frozen']
    list_filter = ['student_class', 'is_frozen']
    search_fields = ['full_name', 'student_id']