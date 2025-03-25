from django.db import models
from django.db.models import Manager
from django.utils.timezone import now
from django.contrib.auth.models import User

class BaseModel(models.Model):
    id = models.AutoField(primary_key=True)  # Auto-incrementing integer ID
    created_date = models.DateTimeField(default=now, editable=False)
    modified_date = models.DateTimeField(default=now)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created_by",
        verbose_name="Created by",
    )
    modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_modified_by",
        verbose_name="Modified by",
    )
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    
    def save(self, *args, **kwargs):
        """
        Update modified_date on save and set created_date only when the object is first created.
        """
        if not self.pk:  # If the instance is being created
            self.created_date = now()
        self.modified_date = now()
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class ActiveManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
