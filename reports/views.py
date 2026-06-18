from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from accounts.permissions import IsAdmin
from students.models import Student
from results.models import Test, Mark
from .pdf_generator import generate_report_card


class ReportCardView(APIView):
    """
    GET /api/reports/report-card/<student_id>/<test_id>/
    Generate and download a PDF report card.
    Admin only.
    """
    permission_classes = [IsAdmin]

    def get(self, request, student_id, test_id):
        student = get_object_or_404(Student, id=student_id)
        test    = get_object_or_404(Test,    id=test_id)

        marks = Mark.objects.filter(
            student=student,
            test=test
        ).select_related('subject').order_by('subject__name')

        if not marks.exists():
            return Response(
                {'error': 'No marks found for this student in this test.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Generate PDF
        buffer = generate_report_card(student, test, marks)

        # Build filename
        filename = (
            f"report_card_{student.student_id}"
            f"_{test.name.replace(' ', '_')}.pdf"
        )

        # Return as downloadable file
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = (
            f'attachment; filename="{filename}"'
        )
        return response


class StudentAllReportsView(APIView):
    """
    GET /api/reports/student/<student_id>/
    List all tests available for report card generation.
    Admin only.
    """
    permission_classes = [IsAdmin]

    def get(self, request, student_id):
        student = get_object_or_404(Student, id=student_id)

        # Get all tests where this student has marks
        tests = Test.objects.filter(
            marks__student=student
        ).distinct().order_by('-date')

        test_list = []
        for test in tests:
            marks = Mark.objects.filter(student=student, test=test)
            total_obtained = sum(m.obtained_marks for m in marks)
            total_marks    = sum(m.total_marks    for m in marks)
            pct = round(
                (total_obtained / total_marks * 100), 2
            ) if total_marks > 0 else 0

            test_list.append({
                'test_id':   test.id,
                'test_name': test.name,
                'date':      str(test.date),
                'percentage': pct,
                'download_url': (
                    f'/api/reports/report-card/{student_id}/{test.id}/'
                ),
            })

        return Response({
            'student':      student.full_name,
            'student_id':   student.student_id,
            'available_reports': test_list,
        })