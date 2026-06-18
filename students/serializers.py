from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Student, Class

User = get_user_model()


class ClassSerializer(serializers.ModelSerializer):
    """
    Serializer for Class model.
    Used to list and create classes.
    """
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = Class
        fields = ['id', 'name', 'board', 'display_name']

    def get_display_name(self, obj):
        return str(obj)  # calls Class.__str__()


class StudentListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing students.
    We don't need every field when showing a list.
    """
    student_class = ClassSerializer(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Student
        fields = [
            'id',
            'full_name',
            'student_id',
            'student_class',
            'username',
            'is_frozen',
            'enrolled_at'
        ]


class StudentDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for viewing a single student.
    """
    student_class = ClassSerializer(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)

    class Meta:
        model = Student
        fields = [
            'id',
            'full_name',
            'student_id',
            'student_class',
            'phone',
            'username',
            'email',
            'is_active',
            'is_frozen',
            'enrolled_at'
        ]


class StudentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new student.
    Also creates the linked User account.
    """
    # These fields are for the User account
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True, required=False)

    # This is for the Student profile
    student_class = serializers.PrimaryKeyRelatedField(
        queryset=Class.objects.all()
    )

    class Meta:
        model = Student
        fields = [
            'full_name',
            'student_id',
            'student_class',
            'phone',
            'username',
            'password',
            'email',
        ]

    def validate_username(self, value):
        """Check username is not already taken."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('This username is already taken.')
        return value

    def validate_student_id(self, value):
        """Check student ID is not already taken."""
        if Student.objects.filter(student_id=value).exists():
            raise serializers.ValidationError('This student ID is already taken.')
        return value

    def create(self, validated_data):
        """
        Create both the User and Student in one transaction.
        If anything fails, neither gets created.
        """
        from django.db import transaction

        username = validated_data.pop('username')
        password = validated_data.pop('password')
        email = validated_data.pop('email', '')

        with transaction.atomic():
            # Create the User account
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                role='student'
            )
            # Create the Student profile
            student = Student.objects.create(
                user=user,
                **validated_data
            )

        return student


class StudentUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating student information.
    Cannot change username or student_id after creation.
    """
    student_class = serializers.PrimaryKeyRelatedField(
        queryset=Class.objects.all()
    )
    email = serializers.EmailField(required=False)

    class Meta:
        model = Student
        fields = [
            'full_name',
            'student_class',
            'phone',
            'email',
        ]

    def update(self, instance, validated_data):
        email = validated_data.pop('email', None)

        # Update student fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update email on user if provided
        if email:
            instance.user.email = email
            instance.user.save()

        return instance