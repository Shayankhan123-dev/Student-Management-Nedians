from rest_framework import serializers
from .models import Subject, Test, Mark
from students.models import Student, Class


class SubjectSerializer(serializers.ModelSerializer):
    """
    Serializer for Subject model.
    """
    class_name = serializers.CharField(
        source='student_class.__str__',
        read_only=True
    )

    class Meta:
        model = Subject
        fields = ['id', 'name', 'student_class', 'class_name']


class TestSerializer(serializers.ModelSerializer):
    """
    Serializer for Test model.
    """
    class_name = serializers.CharField(
        source='student_class.__str__',
        read_only=True
    )

    class Meta:
        model = Test
        fields = [
            'id',
            'name',
            'student_class',
            'class_name',
            'date',
            'description',
            'created_at',
        ]


class MarkSerializer(serializers.ModelSerializer):
    """
    Serializer for reading marks.
    Shows full details.
    """
    student_name = serializers.CharField(
        source='student.full_name',
        read_only=True
    )
    student_id = serializers.CharField(
        source='student.student_id',
        read_only=True
    )
    subject_name = serializers.CharField(
        source='subject.name',
        read_only=True
    )
    test_name = serializers.CharField(
        source='test.name',
        read_only=True
    )
    percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = Mark
        fields = [
            'id',
            'test',
            'test_name',
            'student',
            'student_name',
            'student_id',
            'subject',
            'subject_name',
            'obtained_marks',
            'total_marks',
            'percentage',
        ]


class SingleMarkSerializer(serializers.Serializer):
    """
    Represents one student's mark for one subject in a bulk request.
    """
    student_id = serializers.IntegerField()
    subject_id = serializers.IntegerField()
    obtained_marks = serializers.IntegerField(min_value=0)
    total_marks = serializers.IntegerField(min_value=1)

    def validate(self, data):
        if data['obtained_marks'] > data['total_marks']:
            raise serializers.ValidationError(
                'Obtained marks cannot exceed total marks.'
            )
        return data


class BulkMarkSerializer(serializers.Serializer):
    """
    Serializer for entering marks for an entire test at once.

    Expected input:
    {
        "test_id": 1,
        "marks": [
            {
                "student_id": 1,
                "subject_id": 1,
                "obtained_marks": 85,
                "total_marks": 100
            },
            ...
        ]
    }
    """
    test_id = serializers.IntegerField()
    marks = SingleMarkSerializer(many=True)

    def validate_test_id(self, value):
        if not Test.objects.filter(id=value).exists():
            raise serializers.ValidationError('Test not found.')
        return value

    def validate_marks(self, value):
        if not value:
            raise serializers.ValidationError(
                'At least one mark record is required.'
            )
        return value


class MarkUpdateSerializer(serializers.ModelSerializer):
    """
    For updating a single mark record.
    """
    class Meta:
        model = Mark
        fields = ['obtained_marks', 'total_marks']

    def validate(self, data):
        obtained = data.get(
            'obtained_marks',
            self.instance.obtained_marks
        )
        total = data.get(
            'total_marks',
            self.instance.total_marks
        )
        if obtained > total:
            raise serializers.ValidationError(
                'Obtained marks cannot exceed total marks.'
            )
        return data


class TestDetailSerializer(serializers.ModelSerializer):
    """
    Full test detail including all marks.
    Used when admin views a specific test.
    """
    class_name = serializers.CharField(
        source='student_class.__str__',
        read_only=True
    )
    marks = MarkSerializer(many=True, read_only=True)
    total_students = serializers.SerializerMethodField()
    class_average = serializers.SerializerMethodField()

    class Meta:
        model = Test
        fields = [
            'id',
            'name',
            'student_class',
            'class_name',
            'date',
            'description',
            'created_at',
            'total_students',
            'class_average',
            'marks',
        ]

    def get_total_students(self, obj):
        return obj.marks.values('student').distinct().count()

    def get_class_average(self, obj):
        marks = obj.marks.all()
        if not marks:
            return 0
        total_percentage = sum(m.percentage for m in marks)
        return round(total_percentage / len(marks), 2)