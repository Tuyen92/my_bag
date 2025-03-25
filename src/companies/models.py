from django.db import models
from django.core.validators import RegexValidator, EmailValidator

from shared.models import BaseModel

# Create your models here.
class Company(BaseModel):
    name = models.CharField(
        null=True,
        max_length=255,
        unique=True,
        verbose_name="Company Name",
        help_text="The name of the company."
    )
    address = models.TextField(
        null=True,
        blank=True,
        verbose_name="Address",
        help_text="The physical address of the company."
    )
    location = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Location",
        help_text="City or geographical location of the company."
    )
    postal_code = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Postal Code",
        help_text="The postal or ZIP code of the company.",
        validators=[
            RegexValidator(
                regex=r'^\d{4,10}$',
                message="Postal code must contain 4 to 10 digits.",
                code='invalid_postal_code'
            )
        ]
    )
    email = models.EmailField(
        null=True,
        blank=True,
        verbose_name="Email",
        help_text="Contact email for the company.",
        validators=[EmailValidator()]
    )
    logo = models.CharField(
        max_length=255,
        default="",
        blank=True,
        verbose_name="Company Logo",
        help_text="The logo of the company."
    )
    phone = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        verbose_name="Phone Number",
        help_text="Primary contact number of the company.",
        validators=[
            RegexValidator(
                regex=r'^[+]*[(]{0,1}[0-9]{1,4}[)]{0,1}[-\s\./0-9]*$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
                code='invalid_phone_number'
            )
        ]
    )
    fax = models.CharField(
        max_length=15,
        verbose_name="Fax Number",
        help_text="Fax number of the company.",
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Fax number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
                code='invalid_fax_number'
            )
        ]
    )

    def __str__(self):
        return self.name
