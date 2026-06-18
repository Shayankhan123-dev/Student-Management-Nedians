from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentViewSet, ClassViewSet

router = DefaultRouter()
router.register('students', StudentViewSet, basename='student')
router.register('classes', ClassViewSet, basename='class')

urlpatterns = [
    path('', include(router.urls)),
]