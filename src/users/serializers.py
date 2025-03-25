import uuid
from django.db import IntegrityError
from django.contrib.auth import authenticate
from django.contrib.auth.models import Group, User
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from companies.serializers import CompanyDefaultSerializer
from companies.models import Company

from companies.serializers import CompanySerializer
from .models import UserProfile, OTP
from .services import EmailService, GenOTP
from .exceptions import NeedToRequestNewOTP, OTPEmailNotExists, OTPExpiredOrIncorrect


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # Rename the response key
        return {
            "access_token": data["access"]
        }


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        # Rename the keys
        return {
            "access_token": data["access"],
            "refresh_token": data["refresh"],
        }


class GroupSerializer(serializers.ModelSerializer):
    """
    Serializer for Group model to represent groups a user belongs to.
    """
    class Meta:
        model = Group
        fields = ['name']  # You can include more fields if needed

class UserSerializer(serializers.HyperlinkedModelSerializer):
    full_name = serializers.CharField(source='last_name')  # Map last_name to full_name
    company = CompanySerializer(source='user_profile.company', read_only=True)  # Include company details
    role = serializers.CharField(source='groups.first.name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'company', 'role']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    company = CompanyDefaultSerializer()
    full_name = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['full_name', 'email', 'password', 'company']
        validators = [
            UniqueTogetherValidator(
                queryset=User.objects.filter(is_active=True),
                fields=['email']
            )
        ]

    def create(self, validated_data):
        # Extract company data
        company_data = validated_data.pop('company')

        if User.objects.filter(email=validated_data['email']).exists():
            user = User.objects.filter(email=validated_data['email']).first()
            EmailService.send_otp_email(validated_data['email'])
        
        else:
            # Ensure the company name is either the provided one or a default
            company_name = company_data.get('name', None)
            if not company_name:
                company_data['name'] = validated_data['full_name'] + "_" + str(uuid.uuid4())

            # Create a new company
            company = Company.objects.create(**company_data)

            # Create the user with the company
            user = User.objects.create_user(
                username=validated_data['email'],
                email=validated_data['email'],
                last_name=validated_data['full_name'],
                password=validated_data['password'],
                is_active=False
            )

            # Create UserProfile with user and company, and set is_admin to True
            UserProfile.objects.create(user=user, company=company, is_admin=True)

            # Assign user to a group (e.g., "Admin" group by default)
            default_group = Group.objects.get(name='Admin')  # You can modify this to assign to a different group
            user.groups.add(default_group)  # Add the user to the group
            user.save()  # Save the user after adding to the group

            EmailService.send_otp_email(validated_data['email'])

        return user
    
class UserCreationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    role = serializers.CharField(required=True, help_text="The role of the user (e.g., 'Manager', 'Employee')")
    full_name = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'role', 'full_name']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate(self, attrs):
        """
        Custom validation logic to set `username` as `email`.
        """
        attrs['username'] = attrs.get('email')  # Automatically set `username` to the same value as `email`
        return attrs

    def validate_email(self, email):
        """
        Custom validation for the email field.
        Reactivate inactive users or ensure uniqueness for active users.
        """
        return self._validate_field_uniqueness('email', email)

    def validate_username(self, username):
        """
        Custom validation for the username field.
        Reactivate inactive users or ensure uniqueness for active users.
        """
        return self._validate_field_uniqueness('username', username)

    def _validate_field_uniqueness(self, field_name, value):
        """
        Generic validation to check uniqueness of a field (e.g., email, username).
        Reactivate users if inactive or ensure active uniqueness.
        """
        # Check for active users
        active_user = User.objects.filter(**{field_name: value, 'is_active': True}).first()
        if active_user:
            raise serializers.ValidationError(f"A user with this {field_name} already exists.")

        # Check for inactive users
        inactive_user = User.objects.filter(**{field_name: value, 'is_active': False}).first()
        if inactive_user:
            inactive_user.is_active = True
            inactive_user.save()
            self.context['reactivated_user'] = inactive_user

        return value

    def create(self, validated_data):
        """
        Create a new user and assign them to a company and a role group.
        """
        company = validated_data.pop('company', None)
        role = validated_data.pop('role', None)
        full_name = validated_data.pop('full_name', '')

        try:
            # Create the user
            user = User.objects.create_user(
                email=validated_data['email'],
                username=validated_data['username'],
                password=validated_data['password'],
                last_name=full_name,
            )

            # Assign user to company profile
            if company:
                UserProfile.objects.create(user=user, company=company)

            # Assign user to the group matching the role
            self._assign_user_to_group(user, role)

        except IntegrityError:
            raise serializers.ValidationError(f"This user already exists.")

        return user

    def _assign_user_to_group(self, user, role):
        """
        Assign the user to the specified role group.
        """
        try:
            group = Group.objects.get(name=role)
            user.groups.add(group)
        except Group.DoesNotExist:
            raise serializers.ValidationError({"role": f"The role '{role}' does not exist."})
    

class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value


class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        try:
            GenOTP.verify_otp(data['otp'], data['email'])
        except OTPEmailNotExists:
            raise Exception("Email or OTP does not exist.")
        except NeedToRequestNewOTP:
            raise Exception("Need to request a new OTP.")
        except OTPExpiredOrIncorrect:
            raise Exception("OTP is expired.")

        return data
    

class ResetPassWithOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, required=True)
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        email = data.get("email")
        if not User.objects.filter(email=email, is_active=True).exists():
            raise serializers.ValidationError({"error": "The user with this email does not exist."})

        try:
            GenOTP.verify_otp(data['otp'], data['email'])
        except OTPEmailNotExists:
            raise serializers.ValidationError({"error": "Email or OTP does not exist."})
        except NeedToRequestNewOTP:
            raise serializers.ValidationError({"error": "Need to request a new OTP."})
        except OTPExpiredOrIncorrect:
            raise serializers.ValidationError({"error": "OTP is expired."})

        return data


class UserLoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)
    remember_me = serializers.BooleanField(required=False)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        # Check if the username exists
        user = User.objects.filter(username=email, is_active=True).first()
        if not user:
            raise serializers.ValidationError({"error": "The email does not exist."})

        # Check password
        user = authenticate(username=email, password=password)
        if not user:
            raise serializers.ValidationError({"error": "Invalid password. Please try again."})

        # Add user to validated data for view to access
        data['user'] = user
        return data


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, email):
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError(_("No user is associated with this email address."))
        return email

class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for handling password change requests.
    """
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']
