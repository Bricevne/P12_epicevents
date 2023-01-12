from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    """Custom user model to add a role attribute."""

    class Role(models.TextChoices):
        SALES = 'SA', _('Sales')
        SUPPORT = 'SU', _('Support')
        MANAGEMENT = 'M', _('Management')

    username = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=50, blank=False, null=False)
    last_name = models.CharField(max_length=50, blank=False, null=False)
    role = models.CharField(max_length=2, choices=Role.choices)

    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.username} - {self.role}"

    def save(self, *args, **kwargs):
        self.is_staff = True
        super().save(*args, **kwargs)
        if self.role == "SA":
            group = Group.objects.get(name='sales')
            group.user_set.add(self)
        elif self.role == "SU":
            group = Group.objects.get(name='support')
            group.user_set.add(self)
        elif self.role == "M":
            group = Group.objects.get(name='management')
            group.user_set.add(self)
