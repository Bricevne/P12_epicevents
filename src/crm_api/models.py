from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from eventmanager import settings


class Client(models.Model):
    """Stores a client, related to :model:`authentication.CustomUser`."""
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)
    email = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    mobile = models.CharField(max_length=20)
    company_name = models.CharField(max_length=250)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    sales_contact = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.id}. {self.first_name} {self.last_name} - {self.company_name}"


class Contract(models.Model):
    """Stores a contract, related to :model:`authentication.CustomUser`and :model:`crm_api.Client`."""
    amount = models.FloatField()
    payment_due = models.DateTimeField()
    signed = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    sales_contact = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    client = models.ForeignKey(to=Client, on_delete=models.CASCADE, related_name="contract")

    objects = models.Manager()

    def __str__(self):
        return f"{self.id} - {self.signed}"


class Event(models.Model):
    """Stores an event, related to :model:`authentication.CustomUser`and :model:`crm_api.Contract`."""

    class Status(models.TextChoices):
        TO_DO = 'T', _('To do')
        IN_PROGRESS = 'I', _('In progress')
        COMPLETED = 'C', _('Completed')

    title = models.CharField(max_length=50)
    notes = models.CharField(max_length=200)
    attendees = models.IntegerField()
    status = models.CharField(max_length=1, choices=Status.choices)
    event_date = models.DateTimeField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    support_contact = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    client = models.ForeignKey(to=Client, on_delete=models.CASCADE, related_name='event')

    objects = models.Manager()

    def __str__(self):
        return f"{self.id}. {self.title} - {self.status}"

    def clean(self):
        client = self.client
        contracts = Contract.objects.filter(client=client, signed=True)
        events = Event.objects.filter(client=client)
        if len(contracts) <= len(events) and not self.id:
            raise ValidationError("This client does not have enough signed contracts to create a new event.")