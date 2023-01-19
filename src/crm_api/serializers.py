from rest_framework.serializers import ModelSerializer

from authentication.models import CustomUser
from crm_api.models import Client, Contract, Event


class CustomUserListSerializer(ModelSerializer):
    """User serializer for a list of users."""

    class Meta:
        model = CustomUser
        fields = ["id", "username", "first_name", "last_name", "email", "role"]


class ClientListSerializer(ModelSerializer):
    """Client serializer for a list of clients."""

    class Meta:
        model = Client
        fields = ["id", "first_name", "last_name", "sales_contact"]


class ClientDetailSerializer(ModelSerializer):
    """Project serializer for a detail of a project."""

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
        """Gets a list of comments for a particular issue."""

        queryset = instance.comment.all()
        serializer = ContractListSerializer(queryset, many=True)
        return serializer.data


class ContractListSerializer(ModelSerializer):
    """Project serializer for a list of projects."""

    class Meta:
        model = Contract
        fields = ["id", "amount", "payment_due", "signed", "sales_contact_id", "client_id"]


class ContractDetailSerializer(ModelSerializer):
    """Project serializer for a detail of a project."""

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
        """Gets a list of comments for a particular issue."""

        queryset = instance.event.all()
        serializer = EventListSerializer(queryset, many=True)
        return serializer.data


class ContractSupportSerializer(ModelSerializer):
    """Project serializer for a detail of a project."""

    class Meta:
        model = Contract
        fields = [
            "id",
            "event",
        ]

    def get_event(self, instance):
        """Gets a list of comments for a particular issue."""

        queryset = instance.event.all()
        serializer = EventListSerializer(queryset, many=True)
        return serializer.data



class EventListSerializer(ModelSerializer):
    """Project serializer for a list of projects."""

    class Meta:
        model = Event
        fields = ["id", "title", "description", "guests", "status", "event_date", "support_contact_id", "contract_id"]


class EventDetailSerializer(ModelSerializer):
    """Project serializer for a detail of a project."""

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
