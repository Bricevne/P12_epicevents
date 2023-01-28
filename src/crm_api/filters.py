from django_filters import rest_framework as filters

from authentication.models import CustomUser
from crm_api.models import Client, Contract, Event


class CustomUserFilter(filters.FilterSet):

    class Meta:
        model = CustomUser
        fields = {
            "first_name": ["icontains"],
            "last_name": ["icontains"],
            "role": ["icontains"]
        }


class ClientFilter(filters.FilterSet):

    class Meta:
        model = Client
        fields = {
            "first_name": ["icontains"],
            "last_name": ["icontains"],
            "company_name": ["icontains"]
        }


class ContractFilter(filters.FilterSet):

    class Meta:
        model = Contract
        fields = {
            "amount": ["lte", "gte"],
            "payment_due": ["lte", "gte"],
            "signed": ["icontains"]
        }


class EventFilter(filters.FilterSet):

    class Meta:
        model = Event
        fields = {
            "title": ["icontains"],
            "status": ["icontains"],
            "event_date": ["lte", "gte"]
        }