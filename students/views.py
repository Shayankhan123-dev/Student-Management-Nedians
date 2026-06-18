from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from accounts.permissions import IsAdmin, IsAdminOrStudent
from .models import Student, Class
from .serializers import (
    StudentListSerializer,
    StudentDetailSerializer,
    StudentCreateSerializer,
    StudentUpdateSerializer,
    ClassSerializer
)


class ClassViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing classes.
    Admin only.
    """
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [IsAdmin]


class StudentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing students.
    List, create, retrieve, update → Admin only.
    """
    permission_classes = [IsAdmin]

    def get_queryset(self):
        """
        Allow filtering by class and search by name/ID.
        """
        queryset = Student.objects.select_related(
            'user', 'student_class'
        ).all()

        # Filter by class
        class_id = self.request.query_params.get('class_id')
        if class_id:
            queryset = queryset.filter(student_class_id=class_id)

        # Search by name or student ID
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                full_name__icontains=search
            ) | queryset.filter(
                student_id__icontains=search
            )

        # Filter by frozen status
        is_frozen = self.request.query_params.get('is_frozen')
        if is_frozen is not None:
            queryset = queryset.filter(is_frozen=is_frozen.lower() == 'true')

        return queryset

    def get_serializer_class(self):
        """
        Use different serializers for different actions.
        This is a key DRF pattern.
        """
        if self.action == 'list':
            return StudentListSerializer
        if self.action == 'create':
            return StudentCreateSerializer
        if self.action in ['update', 'partial_update']:
            return StudentUpdateSerializer
        return StudentDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = serializer.save()
        # Return full detail after creation
        return Response(
            StudentDetailSerializer(student).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['patch'], url_path='freeze')
    def freeze(self, request, pk=None):
        """
        PATCH /api/students/{id}/freeze/
        Freeze a student account.
        """
        student = get_object_or_404(Student, pk=pk)
        student.is_frozen = True
        student.save()
        return Response(
            {'message': f'{student.full_name} account has been frozen.'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['patch'], url_path='activate')
    def activate(self, request, pk=None):
        """
        PATCH /api/students/{id}/activate/
        Activate a frozen student account.
        """
        student = get_object_or_404(Student, pk=pk)
        student.is_frozen = False
        student.save()
        return Response(
            {'message': f'{student.full_name} account has been activated.'},
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=['get'],
        url_path='me',
        permission_classes=[IsAdminOrStudent]
    )
    def me(self, request):
        """
        GET /api/students/me/
        Student views their own profile.
        """
        try:
            student = request.user.student_profile
            return Response(StudentDetailSerializer(student).data)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )