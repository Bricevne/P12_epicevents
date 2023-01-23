from django.shortcuts import get_object_or_404
from rest_framework.serializers import ValidationError
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.viewsets import ModelViewSet

from authentication.models import CustomUser
from crm_api import serializers
from crm_api.models import Client, Contract, Event


class MultipleSerializerMixin:
    """Allows the modification of a serializer_class in ViewSets."""
    detail_serializer_class = None
    support_serializer_class = None

    def get_serializer_class(self):
        """Replaces standard serializer_class by another serializer class.

        support_serializer_class: When the requesting user is a support staff. (Only for contracts)
        detail_serializer_class: When retrieving a particular serialized object.
         """
        if self.support_serializer_class is not None and self.request.user.role == "SU":
            return self.support_serializer_class
        if self.action == 'retrieve' and self.detail_serializer_class is not None:
            return self.detail_serializer_class
        return super().get_serializer_class()


class CustomUserViewset(MultipleSerializerMixin, ModelViewSet):
    """Displays users from :model:`authentication.CustomUser`.

    Manages the following endpoints:
    /users
    /users/:user_id
    """

    serializer_class = serializers.CustomUserListSerializer
    detail_serializer_class = None
    permission_classes = (DjangoModelPermissions,)
    http_method_names = ["get", "post", "patch"]

    def get_queryset(self):
        """Gets all users for every staff member."""
        return CustomUser.objects.all()


class ClientViewset(MultipleSerializerMixin, ModelViewSet):
    """Displays clients from :model:`crm_api.Client`.

    Manages the following endpoints:
    /clients
    /clients/:client_id
    """

    serializer_class = serializers.ClientListSerializer
    detail_serializer_class = serializers.ClientDetailSerializer
    permission_classes = (DjangoModelPermissions,)
    http_method_names = ["get", "post", "patch"]

    def get_queryset(self):
        """Gets the suitable queryset depending on the user's group.

        Management and superusers: all clients.
        Sales: all clients whose sales contact is the user.
        Support: all clients whose event's support contact is the user.
        """
        if self.request.user.role == "SA":
            return Client.objects.filter(sales_contact=self.request.user)
        elif self.request.user.role == "SU":
            return Client.objects.filter(
                contract__in=Contract.objects.filter(
                    event__in=Event.objects.filter(
                        support_contact=self.request.user
                    )
                ).distinct("client")
            )
        else:
            return Client.objects.all()

    def perform_create(self, serializer):
        """Defines the [POST] method for a client. Accessible only for sales staff.

        Saves automatically the requesting user as the sales_contact of the client.
        """
        serializer.save(sales_contact=self.request.user)

    def perform_update(self, serializer):
        """Re-defines the [PATCH] method for a client. Accessible only for sales, management staff and superusers.

        Modification: allows the change of the specified sales contact Foreign Key to another sales staff member.
        Accessible only to management staff and superusers.
        """
        try:
            sales_contact_pk = serializer._kwargs['data']['sales_contact']
        except KeyError:
            serializer.save()
        else:
            sales_contact = CustomUser.objects.get(pk=sales_contact_pk)
            if self.request.user.role == "SU":
                raise ValidationError(f"You do not have permissions to change the sales contact.")
            elif self.request.user.role == "SA":
                serializer.save(sales_contact=self.request.user)
            else:
                if not sales_contact.role == "SA":
                    raise ValidationError(f"User {sales_contact.id} is not a sales staff.")
                else:
                    serializer.save(sales_contact=sales_contact)


class ContractViewset(MultipleSerializerMixin, ModelViewSet):
    """Displays contracts from :model:`crm_api.Contract`.

    Manages the following endpoints:
    /clients/:client_id/contracts
    /clients/:client_id/contracts/:contract_id

    Limits contract information for support staff with ContractSupportSerializer.
    """

    serializer_class = serializers.ContractListSerializer
    detail_serializer_class = serializers.ContractDetailSerializer
    support_serializer_class = serializers.ContractSupportSerializer
    permission_classes = (DjangoModelPermissions,)
    http_method_names = ["get", "post", "patch"]

    def get_queryset(self):
        """Gets the suitable queryset depending on the user's group.

        Management and superusers: all contracts from the client.
        Sales: all contracts from the client whose sales contact is the user.
        Support: contracts corresponding to the events they are responsible for. Allowed information: id only.
        """
        if self.request.user.role == "SA":
            return Contract.objects.filter(client_id=self.kwargs['client_pk'], sales_contact=self.request.user)
        elif self.request.user.role == "SU":
            return Contract.objects.filter(
                client_id=self.kwargs['client_pk'],
                event__in=Event.objects.filter(
                    support_contact=self.request.user
                    ).distinct("contract")
                )
        else:
            return Contract.objects.filter(client_id=self.kwargs['client_pk'])

    def perform_create(self, serializer):
        """Defines the [POST] method for a contract. Accessible only for sales staff.

        Saves automatically the requesting user as the sales_contact of the contract
        if he is responsible for the client.
        """
        client = get_object_or_404(Client, pk=self.kwargs['client_pk'])
        if client.sales_contact != self.request.user:
            raise ValidationError("You are not responsible for this client.")
        else:
            serializer.save(sales_contact=self.request.user, client=client)

    def perform_update(self, serializer):
        """Re-defines the [PATCH] method for a contract. Accessible only for sales, management staff and superusers.

        Modification: allows the change of the specified sales contact Foreign Key to another sales staff member.
        Accessible only to management staff and superusers.
        """
        try:
            sales_contact_pk = serializer._kwargs['data']['sales_contact']
        except KeyError:
            serializer.save()
        else:
            sales_contact = CustomUser.objects.get(pk=sales_contact_pk)
            if self.request.user.role == "SU":
                raise ValidationError(f"You do not have permissions to change the sales contact.")
            elif self.request.user.role == "SA":
                serializer.save(sales_contact=self.request.user)
            else:
                if not sales_contact.role == "SA":
                    raise ValidationError(f"User {sales_contact.id} is not a sales staff.")
                else:
                    serializer.save(sales_contact=sales_contact)


class EventViewset(MultipleSerializerMixin, ModelViewSet):
    """Displays events from :model:`crm_api.Event`.

    Manages the following endpoints:
    /clients/:client_id/contracts/:contract_id/events
    /clients/:client_id/contracts/:contract_id/events/:event_id
    """

    serializer_class = serializers.EventListSerializer
    detail_serializer_class = serializers.EventDetailSerializer
    permission_classes = (DjangoModelPermissions,)
    http_method_names = ["get", "post", "patch"]

    def get_queryset(self):
        """Gets the suitable queryset depending on the user's group.

        Management and superusers: all events associated to the contract.
        Sales: none as they do not have group permissions to access events apart from creating them.
        Support: all events (associated to the contract) whose support contact is the user.
        """
        if self.request.user.role == "SU":
            return Event.objects.filter(contract_id=self.kwargs['contract_pk'], support_contact=self.request.user)
        elif self.request.user.role == "SA":
            return Event.objects.none()
        else:
            return Event.objects.filter(contract_id=self.kwargs['contract_pk'])

    def perform_create(self, serializer):
        """Defines the [POST] method for an event. Accessible only for sales staff.

        Sets automatically the support_contact to None.
        """
        contract = get_object_or_404(Contract, pk=self.kwargs['contract_pk'])
        if contract.signed is False:
            raise ValidationError("The contract needs to be signed in order to create an event.")
        if contract.sales_contact != self.request.user:
            raise ValidationError("You are not responsible for this contract.")
        else:
            serializer.save(support_contact=None, contract=contract)

    def perform_update(self, serializer):
        """Re-defines the [PATCH] method for a contract. Accessible only for support, management staff and superusers.

        Modification: allows the change of the specified support_contact Foreign Key to another support staff member.
        Accessible only to management staff and superusers.
        """
        try:
            support_contact_pk = serializer._kwargs['data']['support_contact']
        except KeyError:
            serializer.save()
        else:
            support_contact = CustomUser.objects.get(pk=support_contact_pk)
            if self.request.user.role in ('SU', 'SA'):
                raise ValidationError(f"You do not have permissions to change the support contact.")
            else:
                if support_contact.role != "SU":
                    raise ValidationError(f"User {support_contact.id} is not a support staff.")
                else:
                    serializer.save(support_contact=support_contact)
