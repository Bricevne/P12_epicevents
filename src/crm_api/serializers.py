from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer, CharField

from authentication.models import CustomUser
from crm_api.models import Client, Contract, Event
from django.contrib.auth.password_validation import validate_password


class CustomUserListSerializer(ModelSerializer):
    """Serializes objects from :model:`authentication.CustomUser` for a list of users."""

    password = CharField(write_only=True, required=True, validators=[validate_password])
    password_confirmation = CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ["id", "username", "password", "password_confirmation", "first_name", "last_name", "email", "role"]

    def validate(self, attrs):
        """Validates identical passwords."""

        if attrs['password'] != attrs['password_confirmation']:
            raise ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        """Creates a custom user."""

        user = CustomUser.objects.create(
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
            role=validated_data['role']
        )

        user.set_password(validated_data['password'])
        user.save()
        return user


class ClientListSerializer(ModelSerializer):
    """Serializes objects from :model:`crm_api.Client` for a list of clients."""

    class Meta:
        model = Client
        fields = ["id", "first_name", "last_name", "email", "phone", "mobile", "company_name", "sales_contact"]


class ClientDetailSerializer(ModelSerializer):
    """Serializes objects from :model:`crm_api.Client` for the details of a client."""

    class Meta:
        model = Client
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "mobile",
            "company_name",
            "date_created",
            "date_updated",
            "sales_contact_id",
            "contract"
        ]

    def get_contract(self, instance):
        """Gets the list of existing contracts for a particular client."""
        queryset = instance.comment.all()
        serializer = ContractListSerializer(queryset, many=True)
        return serializer.data


class ContractListSerializer(ModelSerializer):
    """Serializes objects from :model:`crm_api.Contract` for a list of contracts."""

    class Meta:
        model = Contract
        fields = ["id", "amount", "payment_due", "signed", "sales_contact_id", "client_id"]


class ContractDetailSerializer(ModelSerializer):
    """Serializes objects from :model:`crm_api.Contract` for the details of a contract."""

    class Meta:
        model = Contract
        fields = [
            "id",
            "amount",
            "payment_due",
            "signed",
            "date_created",
            "date_updated",
            "sales_contact_id",
            "client_id",
            "event",
        ]

    def get_event(self, instance):
        """Gets the list of existing events for a particular contract."""
        queryset = instance.event.all()
        serializer = EventListSerializer(queryset, many=True)
        return serializer.data


class ContractSupportSerializer(ModelSerializer):
    """Serializes objects from :model:`crm_api.Contract` for contracts when the
    requesting user is from the support group.
    """

    class Meta:
        model = Contract
        fields = [
            "id",
            "event",
        ]

    def get_event(self, instance):
        """Gets the list of existing events for a particular contract."""
        queryset = instance.event.all()
        serializer = EventListSerializer(queryset, many=True)
        return serializer.data


class EventListSerializer(ModelSerializer):
    """Serializes objects from :model:`crm_api.Event` for a list of events."""

    class Meta:
        model = Event
        fields = ["id", "title", "description", "guests", "status", "event_date", "support_contact_id", "contract_id"]


class EventDetailSerializer(ModelSerializer):
    """Serializes objects from :model:`crm_api.Event` for the details of an event."""

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "description",
            "guests",
            "status",
            "event_date",
            "date_created",
            "date_updated",
            "support_contact_id",
            "contract_id",
        ]
