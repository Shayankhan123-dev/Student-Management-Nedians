from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AttendanceViewSet, MyAttendanceView, AttendanceSummaryView

router = DefaultRouter()
router.register('attendance', AttendanceViewSet, basename='attendance')

urlpatterns = [
    # Manual URLs FIRST — before router
    path('attendance/my/', MyAttendanceView.as_view(), name='my-attendance'),
    path(
        'attendance/summary/<int:student_id>/',
        AttendanceSummaryView.as_view(),
        name='attendance-summary'
    ),
    # Router URLs after
    path('', include(router.urls)),
]