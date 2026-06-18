from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from datetime import date
import calendar

from accounts.permissions import IsAdmin, IsAdminOrStudent, IsStudent
from students.models import Student, Class
from .models import Attendance
from .serializers import (
    AttendanceSerializer,
    BulkAttendanceSerializer,
    AttendanceUpdateSerializer,
    AttendanceSummarySerializer,
)


class AttendanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for attendance management.
    """
    permission_classes = [IsAdmin]

    def get_queryset(self):
        """
        Filter attendance by class, date, student, or month.
        """
        queryset = Attendance.objects.select_related(
            'student', 'student_class'
        ).all()

        # Filter by class
        class_id = self.request.query_params.get('class_id')
        if class_id:
            queryset = queryset.filter(student_class_id=class_id)

        # Filter by specific date
        date_param = self.request.query_params.get('date')
        if date_param:
            queryset = queryset.filter(date=date_param)

        # Filter by student
        student_id = self.request.query_params.get('student_id')
        if student_id:
            queryset = queryset.filter(student_id=student_id)

        # Filter by month (format: 2024-10)
        month = self.request.query_params.get('month')
        if month:
            try:
                year, mon = month.split('-')
                queryset = queryset.filter(
                    date__year=year,
                    date__month=mon
                )
            except ValueError:
                pass

        return queryset.order_by('-date')

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return AttendanceUpdateSerializer
        return AttendanceSerializer

    @action(detail=False, methods=['post'], url_path='bulk')
    def bulk_mark(self, request):
        """
        POST /api/attendance/bulk/
        Mark attendance for an entire class at once.
        Uses update_or_create so re-marking same day updates existing records.
        """
        serializer = BulkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        class_id = data['class_id']
        attendance_date = data['date']
        records = data['records']

        student_class = get_object_or_404(Class, id=class_id)

        created_count = 0
        updated_count = 0
        results = []

        for record in records:
            student = get_object_or_404(Student, id=record['student_id'])

            attendance, created = Attendance.objects.update_or_create(
                student=student,
                date=attendance_date,
                defaults={
                    'student_class': student_class,
                    'status': record['status'],
                }
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

            results.append({
                'student_id': student.student_id,
                'student_name': student.full_name,
                'status': attendance.status,
                'action': 'created' if created else 'updated',
            })

        return Response({
            'message': f'Attendance marked for {attendance_date}.',
            'class': str(student_class),
            'created': created_count,
            'updated': updated_count,
            'records': results,
        }, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['get'],
        url_path='class-students',
        permission_classes=[IsAdmin]
    )
    def class_students(self, request):
        """
        GET /api/attendance/class-students/?class_id=1&date=2024-10-15
        Returns all students in a class with their attendance
        status for a given date. Used by admin to pre-fill
        the attendance marking form.
        """
        class_id = request.query_params.get('class_id')
        date_param = request.query_params.get('date')

        if not class_id:
            return Response(
                {'error': 'class_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        student_class = get_object_or_404(Class, id=class_id)
        students = Student.objects.filter(
            student_class=student_class
        ).select_related('user')

        # Get existing attendance for this date if any
        existing = {}
        if date_param:
            attendance_records = Attendance.objects.filter(
                student_class=student_class,
                date=date_param
            )
            existing = {a.student_id: a.status for a in attendance_records}

        result = []
        for student in students:
            result.append({
                'student_db_id': student.id,
                'student_id': student.student_id,
                'full_name': student.full_name,
                'status': existing.get(student.id, None),
                'already_marked': student.id in existing,
            })

        return Response({
            'class': str(student_class),
            'date': date_param,
            'students': result,
        })


class MyAttendanceView(APIView):
    """
    GET /api/attendance/my/
    Student views their own attendance records.
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

        queryset = Attendance.objects.filter(
            student=student
        ).order_by('-date')

        # Filter by month if provided
        month = request.query_params.get('month')
        if month:
            try:
                year, mon = month.split('-')
                queryset = queryset.filter(
                    date__year=year,
                    date__month=mon
                )
            except ValueError:
                pass

        serializer = AttendanceSerializer(queryset, many=True)
        return Response(serializer.data)


class AttendanceSummaryView(APIView):
    """
    GET /api/attendance/summary/{student_id}/
    Returns attendance statistics for a student.
    Used for both admin dashboard and student dashboard.
    """
    permission_classes = [IsAdminOrStudent]

    def get(self, request, student_id):
        # Students can only view their own summary
        if request.user.role == 'student':
            try:
                if request.user.student_profile.id != int(student_id):
                    return Response(
                        {'error': 'You can only view your own attendance.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Exception:
                return Response(
                    {'error': 'Student profile not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )

        student = get_object_or_404(Student, id=student_id)
        records = Attendance.objects.filter(student=student)

        total = records.count()
        present = records.filter(status='PRESENT').count()
        absent = records.filter(status='ABSENT').count()
        percentage = round((present / total * 100), 2) if total > 0 else 0

        # Monthly breakdown
        monthly = {}
        for record in records.order_by('date'):
            key = record.date.strftime('%Y-%m')
            if key not in monthly:
                monthly[key] = {'present': 0, 'absent': 0, 'total': 0}
            monthly[key]['total'] += 1
            if record.status == 'PRESENT':
                monthly[key]['present'] += 1
            else:
                monthly[key]['absent'] += 1

        # Add percentage to each month
        for key in monthly:
            m = monthly[key]
            m['percentage'] = round(
                (m['present'] / m['total'] * 100), 2
            ) if m['total'] > 0 else 0

        return Response({
            'student': student.full_name,
            'student_id': student.student_id,
            'total_classes': total,
            'present': present,
            'absent': absent,
            'attendance_percentage': percentage,
            'monthly_breakdown': monthly,
        })