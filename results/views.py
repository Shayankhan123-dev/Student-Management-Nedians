from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from accounts.permissions import IsAdmin, IsAdminOrStudent
from students.models import Student
from .models import Subject, Test, Mark
from .serializers import (
    SubjectSerializer,
    TestSerializer,
    TestDetailSerializer,
    MarkSerializer,
    MarkUpdateSerializer,
    BulkMarkSerializer,
)


class SubjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing subjects.
    Admin only.
    """
    queryset = Subject.objects.select_related('student_class').all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        queryset = super().get_queryset()
        class_id = self.request.query_params.get('class_id')
        if class_id:
            queryset = queryset.filter(student_class_id=class_id)
        return queryset


class TestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tests/exams.
    Admin only.
    """
    permission_classes = [IsAdmin]

    def get_queryset(self):
        queryset = Test.objects.select_related('student_class').all()

        class_id = self.request.query_params.get('class_id')
        if class_id:
            queryset = queryset.filter(student_class_id=class_id)

        return queryset.order_by('-date')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TestDetailSerializer
        return TestSerializer


class MarkViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing marks.
    """
    permission_classes = [IsAdmin]

    def get_queryset(self):
        queryset = Mark.objects.select_related(
            'test', 'student', 'subject'
        ).all()

        test_id = self.request.query_params.get('test_id')
        if test_id:
            queryset = queryset.filter(test_id=test_id)

        student_id = self.request.query_params.get('student_id')
        if student_id:
            queryset = queryset.filter(student_id=student_id)

        subject_id = self.request.query_params.get('subject_id')
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)

        return queryset

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return MarkUpdateSerializer
        return MarkSerializer

    @action(detail=False, methods=['post'], url_path='bulk')
    def bulk_marks(self, request):
        """
        POST /api/marks/bulk/
        Enter marks for an entire test at once.
        Uses update_or_create so re-entering updates existing records.
        """
        serializer = BulkMarkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        test_id = data['test_id']
        marks_data = data['marks']

        test = get_object_or_404(Test, id=test_id)

        created_count = 0
        updated_count = 0
        results = []
        errors = []

        for mark_data in marks_data:
            student = get_object_or_404(
                Student, id=mark_data['student_id']
            )
            subject = get_object_or_404(
                Subject, id=mark_data['subject_id']
            )

            # Validate student belongs to test's class
            if student.student_class != test.student_class:
                errors.append(
                    f'Student {student.full_name} does not belong '
                    f'to this test class.'
                )
                continue

            # Validate subject belongs to test's class
            if subject.student_class != test.student_class:
                errors.append(
                    f'Subject {subject.name} does not belong '
                    f'to this test class.'
                )
                continue

            mark, created = Mark.objects.update_or_create(
                test=test,
                student=student,
                subject=subject,
                defaults={
                    'obtained_marks': mark_data['obtained_marks'],
                    'total_marks': mark_data['total_marks'],
                }
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

            results.append({
                'student': student.full_name,
                'subject': subject.name,
                'obtained_marks': mark.obtained_marks,
                'total_marks': mark.total_marks,
                'percentage': mark.percentage,
                'action': 'created' if created else 'updated',
            })

        return Response({
            'test': test.name,
            'created': created_count,
            'updated': updated_count,
            'errors': errors,
            'results': results,
        }, status=status.HTTP_200_OK)


class MyResultsView(APIView):
    """
    GET /api/marks/my/
    Student views their own marks.
    """
    permission_classes = [IsAdminOrStudent]

    def get(self, request):
        try:
            student = request.user.student_profile
        except Exception:
            return Response(
                {'error': 'Student profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        queryset = Mark.objects.filter(
            student=student
        ).select_related('test', 'subject').order_by('-test__date')

        # Filter by test if provided
        test_id = request.query_params.get('test_id')
        if test_id:
            queryset = queryset.filter(test_id=test_id)

        serializer = MarkSerializer(queryset, many=True)
        return Response(serializer.data)


class StudentResultSummaryView(APIView):
    """
    GET /api/results/summary/<student_id>/
    Returns full result analytics for a student.
    Used for dashboards.
    """
    permission_classes = [IsAdminOrStudent]

    def get(self, request, student_id):
        # Students can only view their own results
        if request.user.role == 'student':
            try:
                if request.user.student_profile.id != int(student_id):
                    return Response(
                        {'error': 'You can only view your own results.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Exception:
                return Response(
                    {'error': 'Student profile not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )

        student = get_object_or_404(Student, id=student_id)
        marks = Mark.objects.filter(
            student=student
        ).select_related('test', 'subject')

        if not marks:
            return Response({
                'student': student.full_name,
                'student_id': student.student_id,
                'message': 'No results found.',
                'subject_averages': [],
                'test_performance': [],
                'overall_percentage': 0,
            })

        # Subject averages
        subject_data = {}
        for mark in marks:
            name = mark.subject.name
            if name not in subject_data:
                subject_data[name] = {
                    'total_obtained': 0,
                    'total_marks': 0,
                    'count': 0
                }
            subject_data[name]['total_obtained'] += mark.obtained_marks
            subject_data[name]['total_marks'] += mark.total_marks
            subject_data[name]['count'] += 1

        subject_averages = []
        for subject, data in subject_data.items():
            avg = round(
                (data['total_obtained'] / data['total_marks']) * 100, 2
            )
            subject_averages.append({
                'subject': subject,
                'average_percentage': avg,
                'tests_count': data['count'],
            })

        # Test-wise performance
        test_data = {}
        for mark in marks:
            test_name = mark.test.name
            test_date = mark.test.date
            key = f"{mark.test.id}"
            if key not in test_data:
                test_data[key] = {
                    'test_name': test_name,
                    'date': str(test_date),
                    'total_obtained': 0,
                    'total_marks': 0,
                }
            test_data[key]['total_obtained'] += mark.obtained_marks
            test_data[key]['total_marks'] += mark.total_marks

        test_performance = []
        for key, data in test_data.items():
            percentage = round(
                (data['total_obtained'] / data['total_marks']) * 100, 2
            )
            test_performance.append({
                'test_name': data['test_name'],
                'date': data['date'],
                'obtained': data['total_obtained'],
                'total': data['total_marks'],
                'percentage': percentage,
            })

        # Overall percentage
        total_obtained = sum(m.obtained_marks for m in marks)
        total_marks = sum(m.total_marks for m in marks)
        overall = round((total_obtained / total_marks) * 100, 2)

        return Response({
            'student': student.full_name,
            'student_id': student.student_id,
            'overall_percentage': overall,
            'subject_averages': subject_averages,
            'test_performance': sorted(
                test_performance,
                key=lambda x: x['date']
            ),
        })