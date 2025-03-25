import random
import string
from django.db import models
from django.utils import timezone
from django.utils.timezone import now
from django.contrib.auth.models import User

from companies.models import Company


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_profile")
    is_admin = models.BooleanField(default=False)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="users",  # Allows company.users.all() to retrieve all users
        verbose_name="Company",
        help_text="The company this user belongs to."
    )

    def __str__(self):
        return f"{self.user.last_name} - {self.company.name}"

class OTP(models.Model):
    def __str__(self):
        return f'<{self.email}> Verified: {self.isVerified}'

    id = models.BigAutoField(primary_key=True)
    counter = models.IntegerField(default=False)
    mod_time_genotp = models.IntegerField(default=False)
    email = models.CharField( max_length=255, db_comment='Email', null=False, blank=False)
    isVerified = models.BooleanField( db_column='isVerified', default=False)  # Field name made lowercase.
    create_date = models.DateTimeField( default=now, help_text='Date when EmailOTP object was originally created', verbose_name='Created on')

    # def generate_otp(self):
    #     """Generate a random 6-digit OTP"""
    #     otp = ''.join(random.choices(string.digits, k=6))
    #     self.otp_code = otp
    #     self.save()

    # def is_expired(self):
    #     """Check if OTP is expired (5 minutes expiration)"""
    #     expiration_time = self.created_at + timezone.timedelta(minutes=5)
    #     return timezone.now() > expiration_time
