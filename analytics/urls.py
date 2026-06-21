from django.urls import path
from .views import (
    StudentAttendanceAnalyticsView,
    StudentResultsAnalyticsView,
    ClassAttendanceAnalyticsView,
    ClassResultsAnalyticsView,
)

urlpatterns = [
    path(
        'analytics/attendance/<int:student_id>/',
        StudentAttendanceAnalyticsView.as_view(),
        name='student-attendance-analytics'
    ),
    path(
        'analytics/results/<int:student_id>/',
        StudentResultsAnalyticsView.as_view(),
        name='student-results-analytics'
    ),
    path(
        'analytics/class/<int:class_id>/attendance/',
        ClassAttendanceAnalyticsView.as_view(),
        name='class-attendance-analytics'
    ),
    path(
        'analytics/class/<int:class_id>/results/',
        ClassResultsAnalyticsView.as_view(),
        name='class-results-analytics'
    ),
]