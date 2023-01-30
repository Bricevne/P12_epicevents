from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ModelViewSet

from authentication.models import CustomUser
from crm_api import serializers
from crm_api.filters import ClientFilter, CustomUserFilter, ContractFilter, EventFilter
from crm_api.models import Client, Contract, Event
from crm_api.permissions import StaffPermission


class MultipleSerializerMixin:
    """Allows the modification of a serializer_class in ViewSets."""
    detail_serializer_class = None

    def get_serializer_class(self):
        """Replaces standard serializer_class by another serializer class.

        support_serializer_class: When the requesting user is a support staff. (Only for contracts)
        detail_serializer_class: When retrieving a particular serialized object.
         """

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
    permission_classes = (StaffPermission,)
    http_method_names = ["get", "post", "patch", "delete"]
    filterset_class = CustomUserFilter
    perm_slug = "authentication.customuser"

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
    permission_classes = (StaffPermission,)
    http_method_names = ["get", "post", "patch", "delete"]
    filterset_class = ClientFilter
    perm_slug = "crm_api.client"

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
                client_event__in=Event.objects.filter(
                    support_contact=self.request.user
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
                raise ValidationError({"detail": f"You do not have permissions to change the sales contact."})
            elif self.request.user.role == "SA":
                serializer.save(sales_contact=self.request.user)
            else:
                if not sales_contact.role == "SA":
                    raise ValidationError({"detail": f"User {sales_contact.id} is not a sales staff."})
                else:
                    serializer.save(sales_contact=sales_contact)


class ContractViewset(MultipleSerializerMixin, ModelViewSet):
    """Displays contracts from :model:`crm_api.Contract`.

    Manages the following endpoints:
    /clients/:client_id/contracts
    /clients/:client_id/contracts/:contract_id.
    """

    serializer_class = serializers.ContractListSerializer
    detail_serializer_class = serializers.ContractDetailSerializer
    permission_classes = (StaffPermission,)
    http_method_names = ["get", "post", "patch", "delete"]
    filterset_class = ContractFilter
    perm_slug = "crm_api.contract"


    def get_queryset(self):
        """Gets the suitable queryset depending on the user's group.

        Management and superusers: all contracts from the client.
        Sales: all contracts from the client whose sales contact is the user.
        Support: no contract.
        """
        if self.request.user.role == "SA":
            return Contract.objects.filter(client_id=self.kwargs['client_pk'], sales_contact=self.request.user)
        else:
            return Contract.objects.filter(client_id=self.kwargs['client_pk'])

    def perform_create(self, serializer):
        """Defines the [POST] method for a contract. Accessible only for sales staff.

        Saves automatically the requesting user as the sales_contact of the contract
        if he is responsible for the client.
        """
        client = get_object_or_404(Client, pk=self.kwargs['client_pk'])
        if client.sales_contact != self.request.user:
            raise ValidationError({"detail": "You are not responsible for this client."})
        else:
            serializer.save(sales_contact=self.request.user, client=client)

    def perform_update(self, serializer):
        """Re-defines the [PATCH] method for a contract. Accessible only for sales, management staff and superusers.

        Modification: allows the change of the specified sales contact Foreign Key to another sales staff member.
        Accessible only to management staff and superusers.
        """
        sales_contact = ""
        client = ""

        try:
            sales_contact_pk = serializer._kwargs['data']['sales_contact_id']
        except KeyError:
            pass
        else:
            sales_contact = get_object_or_404(CustomUser, pk=sales_contact_pk)

        try:
            client_pk = serializer._kwargs['data']['client_id']
        except KeyError:
            pass
        else:
            client = get_object_or_404(Client, pk=client_pk)

        if sales_contact and self.request.user.role == "SA":
            raise ValidationError({"detail": "You do not have permissions to change the sales contact."})

        if sales_contact and client:
            if self.request.user.role == "SA" and client not in self.request.user.client:
                raise ValidationError({
                    "detail": "You do not have permissions to change the contract to a client you don't have."
                })
            if sales_contact.role != "SA":
                raise ValidationError({"detail": f"User {sales_contact.id} is not a sales staff."})
            serializer.save(sales_contact=sales_contact, client=client)
        elif sales_contact and not client:
            if not sales_contact.role == "SA":
                raise ValidationError({"detail": f"User {sales_contact.id} is not a sales staff."})
            serializer.save(sales_contact=sales_contact)

        elif not sales_contact and client:
            if self.request.user.role == "SA" and client not in self.request.user.client.all():
                raise ValidationError({"detail": f"You do not have permissions to change the contract to a client you don't have."})
            else:
                serializer.save(client=client)
        else:
            super().perform_update(serializer)


class EventViewset(MultipleSerializerMixin, ModelViewSet):
    """Displays events from :model:`crm_api.Event`.

    Manages the following endpoints:
    /clients/:client_id/events
    /clients/:client_id/events/:event_id
    """

    serializer_class = serializers.EventListSerializer
    detail_serializer_class = serializers.EventDetailSerializer
    permission_classes = (StaffPermission,)
    http_method_names = ["get", "post", "patch", "delete"]
    filterset_class = EventFilter
    perm_slug = "crm_api.event"

    def get_queryset(self):
        """Gets the suitable queryset depending on the user's group.

        Management and superusers: all events associated to the client.
        Sales: no event.
        Support: all events (associated to the client) whose support contact is the user.
        """
        if self.request.user.role == "SU":
            return Event.objects.filter(client_id=self.kwargs['client_pk'], support_contact=self.request.user)
        else:
            return Event.objects.filter(client_id=self.kwargs['client_pk'])

    def perform_create(self, serializer):
        """Defines the [POST] method for an event. Accessible only for sales staff.

        Sets automatically the support_contact to None.
        """
        client = get_object_or_404(Client, pk=self.kwargs['client_pk'])
        contract_id = self.request.data.get("contract_id")
        contract = get_object_or_404(Contract, pk=contract_id)
        if client.sales_contact != self.request.user:
            raise ValidationError({"detail": "You are not responsible for this client."})
        if contract.signed is False:
            raise ValidationError({"detail": "The contract needs to be signed in order to create an event."})
        if contract.contract_event.count() == 1:
            raise ValidationError({"detail": "There is already an event for this contract."})
        else:
            serializer.save(support_contact=None, client_id=self.kwargs['client_pk'], contract_id=contract_id)

    def perform_update(self, serializer):
        """Re-defines the [PATCH] method for a contract. Accessible only for support, management staff and superusers.

        Modification: allows the change of the specified support_contact Foreign Key to another support staff member.
        Accessible only to management staff and superusers.
        """

        support_contact = ""
        client = ""
        contract = ""

        try:
            support_contact_pk = serializer._kwargs['data']['support_contact_id']
        except KeyError:
            pass
        else:
            support_contact = get_object_or_404(CustomUser, pk=support_contact_pk)

        try:
            client_pk = serializer._kwargs['data']['client_id']
        except KeyError:
            pass
        else:
            client = get_object_or_404(Client, pk=client_pk)

        try:
            contract_pk = serializer._kwargs['data']['contract_id']
        except KeyError:
            pass
        else:
            contract = get_object_or_404(Contract, pk=contract_pk)

        if self.request.user.role == "SU" and (contract or client or support_contact):
            raise ValidationError("You can't change the contract id, client id or support contact")
        elif self.request.user.role == "SU":
            super().perform_update(serializer)
        else:
            if support_contact:
                if support_contact.role != "SU":
                    raise ValidationError({"detail": f"User {support_contact.id} is not a support staff."})

            if contract:
                if contract.signed is False:
                    raise ValidationError({"detail": f"This contract is not signed."})
                if client:
                    if contract.client != client:
                        raise ValidationError({"detail": f"This contract is not attributed to this client."})

            try:
                if support_contact and contract and client:
                    serializer.save(support_contact=support_contact, contract=contract, client=client)
                elif support_contact and contract and not client:
                    serializer.save(support_contact=support_contact, contract=contract)
                elif support_contact and not contract and client:
                    serializer.save(support_contact=support_contact, client=client)
                elif not support_contact and contract and client:
                    serializer.save(contract=contract, client=client)
                elif not support_contact and not contract and client:
                    serializer.save(client=client)
                elif support_contact and not contract and not client:
                    serializer.save(support_contact=support_contact)
                elif not support_contact and contract and not client:
                    serializer.save(contract=contract)
                else:
                    super().perform_update(serializer)
            except IntegrityError:
                raise ValidationError({"detail": "This contract already has an event"})
