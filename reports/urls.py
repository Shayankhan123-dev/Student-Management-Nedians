from django.urls import path
from .views import ReportCardView, StudentAllReportsView

urlpatterns = [
    path(
        'reports/report-card/<int:student_id>/<int:test_id>/',
        ReportCardView.as_view(),
        name='report-card'
    ),
    path(
        'reports/student/<int:student_id>/',
        StudentAllReportsView.as_view(),
        name='student-reports'
    ),
]