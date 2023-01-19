from django.contrib import admin

from authentication.models import CustomUser
from crm_api.models import Client, Contract, Event


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Class managing clients in admin panel."""
    list_display = ("id", "email", "company_name", "sales_contact", 'date_created', "date_updated")
    list_filter = ("sales_contact",)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.sales_contact = request.user
        super(ClientAdmin, self).save_model(request, obj, form, change)

    def get_fields(self, request, obj=None):
        fields = super(ClientAdmin, self).get_fields(request, obj)
        if not obj or request.user.role != "M":
            fields.remove('sales_contact')
        return fields

    def get_queryset(self, request):
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
        if db_field.name == "sales_contact":
            kwargs['queryset'] = CustomUser.objects.filter(role="SA")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    """Class managing contracts in admin panel."""

    list_display = ("id", "amount", "payment_due", "signed", "sales_contact", "client",)
    list_filter = ("sales_contact", "client",)
    search_fields = ("sales_contact",)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.sales_contact = request.user
        super(ContractAdmin, self).save_model(request, obj, form, change)

    def get_fields(self, request, obj=None):
        fields = super(ContractAdmin, self).get_fields(request, obj)
        if not obj or request.user.role != "M":
            fields.remove('sales_contact')
        return fields

    def get_queryset(self, request):
        if request.user.role == "SA":
            return Contract.objects.filter(sales_contact=request.user.id)
        else:
            return Contract.objects.all()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "sales_contact":
            kwargs['queryset'] = CustomUser.objects.filter(role="SA")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Class managing events in admin panel."""

    list_display = ("id", "title", "status", "event_date", "support_contact", "contract", "client")
    list_filter = ("contract", "support_contact")

    @admin.display(description='client')
    def client(self, obj):
        return obj.contract.client

    def save_model(self, request, obj, form, change):
        if not change:
            obj.support_contact = None
        super(EventAdmin, self).save_model(request, obj, form, change)

    def get_fields(self, request, obj=None):
        fields = super(EventAdmin, self).get_fields(request, obj)
        if not obj or request.user.role in ("SA", "SU"):
            fields.remove('support_contact')
        return fields

    def get_queryset(self, request):
        if request.user.role == "SU":
            return Event.objects.filter(support_contact=request.user.id)
        else:
            return Event.objects.all()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "contract":
            kwargs['queryset'] = Contract.objects.filter(signed=True)
        if db_field.name == "support_contact":
            kwargs['queryset'] = CustomUser.objects.filter(role="SU")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
