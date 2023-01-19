from django.contrib import admin

from authentication.models import CustomUser
from crm_api.models import Client, Contract, Event


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Defines how clients appear in the admin panel."""
    list_display = ("id", "email", "company_name", "sales_contact", 'date_created', "date_updated")
    list_filter = ("sales_contact",)

    def save_model(self, request, obj, form, change):
        """Sets the client's sales contact to the creator when creating a new client."""
        if not change:
            obj.sales_contact = request.user
        super(ClientAdmin, self).save_model(request, obj, form, change)

    def get_fields(self, request, obj=None):
        """Removes the sales_contact field when the user is in sales or support group."""
        fields = super(ClientAdmin, self).get_fields(request, obj)
        if not obj or request.user.role in ("SA", "SU"):
            fields.remove('sales_contact')
        return fields

    def get_queryset(self, request):
        """Gets the suitable queryset depending on the user's group.

        Management and superusers: all clients.
        Sales: all clients whose sales contact is the user.
        Support: all clients whose event's support contact is the user.
        """
        if request.user.role == "SA":
            return Client.objects.filter(sales_contact=request.user.id)
        elif request.user.role == "SU":

            return Client.objects.filter(
                contract__in=Contract.objects.filter(
                    event__in=Event.objects.filter(
                        support_contact=request.user
                    )
                )
            )
        else:
            return Client.objects.all()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Sets the sales_contact field's choices to staff users from the sales group only."""
        if db_field.name == "sales_contact":
            kwargs['queryset'] = CustomUser.objects.filter(role="SA")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    """Defines how contracts appear in the admin panel."""

    list_display = ("id", "amount", "payment_due", "signed", "sales_contact", "client",)
    list_filter = ("sales_contact", "client",)
    search_fields = ("sales_contact",)

    def save_model(self, request, obj, form, change):
        """Sets the contract's sales contact to the creator when creating a new contract."""
        if not change:
            obj.sales_contact = request.user
        super(ContractAdmin, self).save_model(request, obj, form, change)

    def get_fields(self, request, obj=None):
        """Removes the sales_contact field when the user is in sales or support group."""
        fields = super(ContractAdmin, self).get_fields(request, obj)
        if not obj or request.user.role in ("SA", "SU"):
            fields.remove('sales_contact')
        return fields

    def get_queryset(self, request):
        """Gets the suitable queryset depending on the user's group.

        Management and superusers: all contracts.
        Sales: all contracts whose sales contact is the user.
        Support: not specified as they do not have group permissions to access contracts in any way.
        """
        if request.user.role == "SA":
            return Contract.objects.filter(sales_contact=request.user.id)
        else:
            return Contract.objects.all()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Sets the sales_contact field's choices to staff users from the sales group only."""
        if db_field.name == "sales_contact":
            kwargs['queryset'] = CustomUser.objects.filter(role="SA")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Defines how events appear in the admin panel."""

    list_display = ("id", "title", "status", "event_date", "support_contact", "contract", "client")
    list_filter = ("contract", "support_contact")

    @admin.display(description='client')
    def client(self, obj):
        """Adds the client to the event's information in the admin panel."""
        return obj.contract.client

    def save_model(self, request, obj, form, change):
        """Sets the event's support contact to no one when creating a new event."""
        if not change:
            obj.support_contact = None
        super(EventAdmin, self).save_model(request, obj, form, change)

    def get_fields(self, request, obj=None):
        """Removes the support_contact field when the user is in sales or support group."""
        fields = super(EventAdmin, self).get_fields(request, obj)
        if not obj or request.user.role in ("SA", "SU"):
            fields.remove('support_contact')
        return fields

    def get_queryset(self, request):
        """Gets the suitable queryset depending on the user's group.

        Management and superusers: all events.
        Sales: not specified as they do not have group permissions to access events apart from creating them.
        Support: all events whose support contact is the user.
        """
        if request.user.role == "SU":
            return Event.objects.filter(support_contact=request.user.id)
        else:
            return Event.objects.all()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Sets the contract field's choices to signed contracts only.
        Sets the support_contact field's choices to staff users from the support group only..
        """
        if db_field.name == "contract":
            kwargs['queryset'] = Contract.objects.filter(signed=True)
        if db_field.name == "support_contact":
            kwargs['queryset'] = CustomUser.objects.filter(role="SU")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
