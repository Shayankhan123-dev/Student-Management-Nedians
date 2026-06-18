from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Sum, Count, Q
from collections import defaultdict

from accounts.permissions import IsAdmin, IsAdminOrStudent
from students.models import Student, Class
from attendance.models import Attendance
from results.models import Mark, Test, Subject


class StudentAttendanceAnalyticsView(APIView):
    """
    GET /api/analytics/attendance/<student_id>/
    Returns attendance analytics and chart data for one student.
    """
    permission_classes = [IsAdminOrStudent]

    def get(self, request, student_id):
        # Students can only view their own analytics
        if request.user.role == 'student':
            try:
                if request.user.student_profile.id != int(student_id):
                    return Response(
                        {'error': 'You can only view your own analytics.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Exception:
                return Response(
                    {'error': 'Student profile not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )

        student = get_object_or_404(Student, id=student_id)
        records = Attendance.objects.filter(
            student=student
        ).order_by('date')

        total = records.count()
        present = records.filter(status='PRESENT').count()
        absent = records.filter(status='ABSENT').count()
        percentage = round((present / total * 100), 2) if total > 0 else 0

        # --- Chart 1: Monthly attendance bar chart ---
        # Format: [{"month": "Oct 2024", "present": 20, "absent": 3, "percentage": 87}]
        monthly_data = defaultdict(lambda: {'present': 0, 'absent': 0})
        for record in records:
            key = record.date.strftime('%b %Y')
            if record.status == 'PRESENT':
                monthly_data[key]['present'] += 1
            else:
                monthly_data[key]['absent'] += 1

        monthly_chart = []
        for month, data in monthly_data.items():
            total_month = data['present'] + data['absent']
            monthly_chart.append({
                'month': month,
                'present': data['present'],
                'absent': data['absent'],
                'total': total_month,
                'percentage': round(
                    (data['present'] / total_month * 100), 2
                ) if total_month > 0 else 0
            })

        # --- Chart 2: Attendance trend line chart ---
        # Format: [{"date": "2024-10-01", "status": 1}]
        # 1 = present, 0 = absent — easy to plot as a line
        trend_chart = []
        for record in records:
            trend_chart.append({
                'date': str(record.date),
                'status': 1 if record.status == 'PRESENT' else 0,
                'label': record.status,
            })

        return Response({
            'student': student.full_name,
            'student_id': student.student_id,
            'summary': {
                'total_classes': total,
                'present': present,
                'absent': absent,
                'attendance_percentage': percentage,
            },
            'monthly_chart': monthly_chart,
            'trend_chart': trend_chart,
        })


class StudentResultsAnalyticsView(APIView):
    """
    GET /api/analytics/results/<student_id>/
    Returns results analytics and chart data for one student.
    """
    permission_classes = [IsAdminOrStudent]

    def get(self, request, student_id):
        # Students can only view their own analytics
        if request.user.role == 'student':
            try:
                if request.user.student_profile.id != int(student_id):
                    return Response(
                        {'error': 'You can only view your own analytics.'},
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
        ).select_related('test', 'subject').order_by('test__date')

        if not marks.exists():
            return Response({
                'student': student.full_name,
                'student_id': student.student_id,
                'summary': {
                    'overall_percentage': 0,
                    'total_tests': 0,
                    'best_subject': None,
                    'weakest_subject': None,
                },
                'subject_chart': [],
                'test_chart': [],
                'comparison_chart': [],
            })

        # --- Summary stats ---
        total_obtained = sum(m.obtained_marks for m in marks)
        total_marks = sum(m.total_marks for m in marks)
        overall = round((total_obtained / total_marks) * 100, 2)
        total_tests = marks.values('test').distinct().count()

        # --- Chart 1: Subject performance bar chart ---
        # Format: [{"subject": "Math", "average": 85.5, "tests": 3}]
        subject_data = defaultdict(
            lambda: {'obtained': 0, 'total': 0, 'count': 0}
        )
        for mark in marks:
            name = mark.subject.name
            subject_data[name]['obtained'] += mark.obtained_marks
            subject_data[name]['total'] += mark.total_marks
            subject_data[name]['count'] += 1

        subject_chart = []
        for subject, data in subject_data.items():
            avg = round((data['obtained'] / data['total']) * 100, 2)
            subject_chart.append({
                'subject': subject,
                'average': avg,
                'tests': data['count'],
            })

        # Find best and weakest subject
        if subject_chart:
            best = max(subject_chart, key=lambda x: x['average'])
            weakest = min(subject_chart, key=lambda x: x['average'])
        else:
            best = weakest = None

        # --- Chart 2: Test performance line chart ---
        # Format: [{"test": "Unit Test 1", "date": "...", "percentage": 82}]
        test_data = defaultdict(
            lambda: {'name': '', 'date': '', 'obtained': 0, 'total': 0}
        )
        for mark in marks:
            key = str(mark.test.id)
            test_data[key]['name'] = mark.test.name
            test_data[key]['date'] = str(mark.test.date)
            test_data[key]['obtained'] += mark.obtained_marks
            test_data[key]['total'] += mark.total_marks

        test_chart = []
        for key, data in test_data.items():
            pct = round((data['obtained'] / data['total']) * 100, 2)
            test_chart.append({
                'test': data['name'],
                'date': data['date'],
                'obtained': data['obtained'],
                'total': data['total'],
                'percentage': pct,
            })

        # Sort by date
        test_chart = sorted(test_chart, key=lambda x: x['date'])

        # --- Chart 3: Subject comparison across tests ---
        # Format: [{"test": "Unit Test 1", "Math": 85, "Physics": 72}]
        comparison = defaultdict(dict)
        for mark in marks:
            test_name = mark.test.name
            subject_name = mark.subject.name
            pct = mark.percentage
            comparison[test_name][subject_name] = pct
            comparison[test_name]['test'] = test_name
            comparison[test_name]['date'] = str(mark.test.date)

        comparison_chart = sorted(
            list(comparison.values()),
            key=lambda x: x['date']
        )

        return Response({
            'student': student.full_name,
            'student_id': student.student_id,
            'summary': {
                'overall_percentage': overall,
                'total_tests': total_tests,
                'best_subject': best['subject'] if best else None,
                'weakest_subject': weakest['subject'] if weakest else None,
            },
            'subject_chart': subject_chart,
            'test_chart': test_chart,
            'comparison_chart': comparison_chart,
        })


class ClassAttendanceAnalyticsView(APIView):
    """
    GET /api/analytics/class/<class_id>/attendance/
    Returns attendance analytics for an entire class.
    Admin only.
    """
    permission_classes = [IsAdmin]

    def get(self, request, class_id):
        student_class = get_object_or_404(Class, id=class_id)
        students = Student.objects.filter(student_class=student_class)

        if not students.exists():
            return Response({
                'class': str(student_class),
                'message': 'No students in this class.',
                'student_summaries': [],
            })

        student_summaries = []
        for student in students:
            records = Attendance.objects.filter(student=student)
            total = records.count()
            present = records.filter(status='PRESENT').count()
            pct = round((present / total * 100), 2) if total > 0 else 0

            student_summaries.append({
                'student_id': student.student_id,
                'full_name': student.full_name,
                'total': total,
                'present': present,
                'absent': total - present,
                'percentage': pct,
            })

        # Sort by percentage descending
        student_summaries = sorted(
            student_summaries,
            key=lambda x: x['percentage'],
            reverse=True
        )

        # Class average
        if student_summaries:
            class_avg = round(
                sum(s['percentage'] for s in student_summaries) /
                len(student_summaries), 2
            )
        else:
            class_avg = 0

        return Response({
            'class': str(student_class),
            'class_average_attendance': class_avg,
            'total_students': len(student_summaries),
            'student_summaries': student_summaries,
        })


class ClassResultsAnalyticsView(APIView):
    """
    GET /api/analytics/class/<class_id>/results/
    Returns results analytics for an entire class.
    Admin only.
    """
    permission_classes = [IsAdmin]

    def get(self, request, class_id):
        student_class = get_object_or_404(Class, id=class_id)
        students = Student.objects.filter(student_class=student_class)
        tests = Test.objects.filter(student_class=student_class)

        if not tests.exists():
            return Response({
                'class': str(student_class),
                'message': 'No tests found for this class.',
                'student_summaries': [],
                'test_summaries': [],
            })

        # Per student overall performance
        student_summaries = []
        for student in students:
            marks = Mark.objects.filter(student=student)
            if not marks.exists():
                continue
            total_obtained = sum(m.obtained_marks for m in marks)
            total_marks = sum(m.total_marks for m in marks)
            pct = round((total_obtained / total_marks) * 100, 2)
            student_summaries.append({
                'student_id': student.student_id,
                'full_name': student.full_name,
                'overall_percentage': pct,
            })

        student_summaries = sorted(
            student_summaries,
            key=lambda x: x['overall_percentage'],
            reverse=True
        )

        # Per test class average
        test_summaries = []
        for test in tests.order_by('date'):
            marks = Mark.objects.filter(test=test)
            if not marks.exists():
                continue
            total_obtained = sum(m.obtained_marks for m in marks)
            total_marks = sum(m.total_marks for m in marks)
            avg = round((total_obtained / total_marks) * 100, 2)
            test_summaries.append({
                'test': test.name,
                'date': str(test.date),
                'class_average': avg,
                'students_appeared': marks.values(
                    'student'
                ).distinct().count(),
            })

        return Response({
            'class': str(student_class),
            'total_students': students.count(),
            'total_tests': tests.count(),
            'student_summaries': student_summaries,
            'test_summaries': test_summaries,
        })