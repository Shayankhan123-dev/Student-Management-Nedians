from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SubjectViewSet,
    TestViewSet,
    MarkViewSet,
    MyResultsView,
    StudentResultSummaryView,
)

router = DefaultRouter()
router.register('subjects', SubjectViewSet, basename='subject')
router.register('tests', TestViewSet, basename='test')
router.register('marks', MarkViewSet, basename='mark')

urlpatterns = [
    # Manual URLs FIRST
    path('marks/my/', MyResultsView.as_view(), name='my-results'),
    path(
        'results/summary/<int:student_id>/',
        StudentResultSummaryView.as_view(),
        name='results-summary'
    ),
    # Router URLs after
    path('', include(router.urls)),
]