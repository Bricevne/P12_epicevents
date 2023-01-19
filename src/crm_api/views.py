from django.shortcuts import get_object_or_404
from rest_framework.serializers import ValidationError
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.viewsets import ModelViewSet

from authentication.models import CustomUser
from crm_api import serializers
from crm_api.models import Client, Contract, Event


class MultipleSerializerMixin:
    """
    Mixin allowing the change of a serializer_class in ViewSets.
    """
    detail_serializer_class = None
    support_serializer_class = None

    def get_serializer_class(self):
        """
        Replaces standard serializer_class by a detail_serializer_class when viewing an object detail.
        """
        if self.support_serializer_class is not None and self.request.user.role == "SU":
            return self.support_serializer_class
        if self.action == 'retrieve' and self.detail_serializer_class is not None:
            return self.detail_serializer_class
        return super().get_serializer_class()


class CustomUserViewset(MultipleSerializerMixin, ModelViewSet):
    """
    Class managing the following endpoints:
    /projects
    /projects/:project_id
    """

    serializer_class = serializers.CustomUserListSerializer
    detail_serializer_class = None
    permission_classes = (DjangoModelPermissions,)

    def get_queryset(self):
        """
        Defines the queryset.
        """
        return CustomUser.objects.all()


class ClientViewset(MultipleSerializerMixin, ModelViewSet):
    """
    Class managing the following endpoints:
    /projects
    /projects/:project_id
    """

    serializer_class = serializers.ClientListSerializer
    detail_serializer_class = serializers.ClientDetailSerializer
    permission_classes = (DjangoModelPermissions,)
    http_method_names = ["get", "post", "patch"]

    def get_queryset(self):
        """
        Defines the queryset.
        """
        if self.request.user.role == "M":
            return Client.objects.all()
        elif self.request.user.role == "SA":
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
        """
        Defines the creation [POST] of a project.
        Automatically saves the corresponding author of the project.
        """
        serializer.save(sales_contact=self.request.user)

    def perform_update(self, serializer):
        """
        Re-defines the modification [PATCH] of a contract.
        Allows the change of the specified assignee user Foreign Key.
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
    """
    Class managing the following endpoints:
    /projects
    /projects/:project_id
    """

    serializer_class = serializers.ContractListSerializer
    detail_serializer_class = serializers.ContractDetailSerializer
    support_serializer_class = serializers.ContractSupportSerializer
    permission_classes = (DjangoModelPermissions,)
    http_method_names = ["get", "post", "patch"]

    def get_queryset(self):
        """
        Defines the queryset.
        """
        if self.request.user.role == "M":
            return Contract.objects.filter(client_id=self.kwargs['client_pk'])
        elif self.request.user.role == "SA":
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
        """
        Defines the creation [POST] of a project.
        Automatically saves the corresponding author of the project.
        """
        client = get_object_or_404(Client, pk=self.kwargs['client_pk'])
        if client.sales_contact != self.request.user:
            raise ValidationError("You are not responsible for this client.")
        else:
            serializer.save(sales_contact=self.request.user, client=client)

    def perform_update(self, serializer):
        """
        Re-defines the modification [PUT] of an issue.
        Allows the change of the specified assignee user Foreign Key.
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
    """
    Class managing the following endpoints:
    /projects
    /projects/:project_id
    """

    serializer_class = serializers.EventListSerializer
    detail_serializer_class = serializers.EventDetailSerializer
    permission_classes = (DjangoModelPermissions,)
    http_method_names = ["get", "post", "patch"]

    def get_queryset(self):
        """
        Defines the queryset.
        """
        if self.request.user.role == "M":
            return Event.objects.filter(contract_id=self.kwargs['contract_pk'])
        elif self.request.user.role == "SU":
            return Event.objects.filter(contract_id=self.kwargs['contract_pk'], support_contact=self.request.user)
        elif self.request.user.role == "SA":
            return Event.objects.none()
        else:
            return Event.objects.filter(contract_id=self.kwargs['contract_pk'])

    def perform_create(self, serializer):
        """
        Defines the creation [POST] of a project.
        Automatically saves the corresponding author of the project.
        """
        contract = get_object_or_404(Contract, pk=self.kwargs['contract_pk'])
        if contract.sales_contact != self.request.user:
            raise ValidationError("You are not responsible for this contract.")
        else:
            serializer.save(support_contact=None, contract=contract)

    def perform_update(self, serializer):
        """
        Re-defines the modification [PUT] of an issue.
        Allows the change of the specified assignee user Foreign Key.
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
