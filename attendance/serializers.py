from rest_framework import serializers
from .models import Attendance
from students.models import Student, Class
from students.serializers import StudentListSerializer, ClassSerializer


class AttendanceSerializer(serializers.ModelSerializer):
    """
    Serializer for reading attendance records.
    Shows full student and class details.
    """
    student_name = serializers.CharField(
        source='student.full_name',
        read_only=True
    )
    student_id = serializers.CharField(
        source='student.student_id',
        read_only=True
    )
    class_name = serializers.CharField(
        source='student_class.__str__',
        read_only=True
    )

    class Meta:
        model = Attendance
        fields = [
            'id',
            'student',
            'student_name',
            'student_id',
            'student_class',
            'class_name',
            'date',
            'status',
            'marked_at',
            'updated_at',
        ]


class SingleAttendanceRecordSerializer(serializers.Serializer):
    """
    Represents one student's attendance in a bulk request.
    """
    student_id = serializers.IntegerField()
    status = serializers.ChoiceField(
        choices=['PRESENT', 'ABSENT']
    )


class BulkAttendanceSerializer(serializers.Serializer):
    """
    Serializer for marking attendance for an entire class at once.

    Expected input:
    {
        "class_id": 1,
        "date": "2024-10-15",
        "records": [
            {"student_id": 1, "status": "PRESENT"},
            {"student_id": 2, "status": "ABSENT"}
        ]
    }
    """
    class_id = serializers.IntegerField()
    date = serializers.DateField()
    records = SingleAttendanceRecordSerializer(many=True)

    def validate_class_id(self, value):
        if not Class.objects.filter(id=value).exists():
            raise serializers.ValidationError('Class not found.')
        return value

    def validate_records(self, value):
        if not value:
            raise serializers.ValidationError(
                'At least one attendance record is required.'
            )
        return value

    def validate(self, data):
        """
        Make sure all student IDs in records belong to the given class.
        """
        class_id = data.get('class_id')
        records = data.get('records', [])

        student_ids = [r['student_id'] for r in records]
        valid_students = Student.objects.filter(
            student_class_id=class_id,
            id__in=student_ids
        ).values_list('id', flat=True)

        invalid_ids = set(student_ids) - set(valid_students)
        if invalid_ids:
            raise serializers.ValidationError(
                f'Students {invalid_ids} do not belong to this class.'
            )

        return data


class AttendanceUpdateSerializer(serializers.ModelSerializer):
    """
    For updating a single attendance record.
    Only status can be changed.
    """
    class Meta:
        model = Attendance
        fields = ['status']


class AttendanceSummarySerializer(serializers.Serializer):
    """
    For returning attendance statistics.
    """
    total_classes = serializers.IntegerField()
    present = serializers.IntegerField()
    absent = serializers.IntegerField()
    attendance_percentage = serializers.FloatField()
    monthly_breakdown = serializers.DictField()