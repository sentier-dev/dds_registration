import zipfile
from io import BytesIO

from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Q
from django.http import HttpResponse

from .forms import (
    EventAdminForm,
    PaymentAdminForm,
    RegistrationOptionAdminForm,
    UserAdminForm,
)
from .models import (
    Event,
    Membership,
    Message,
    Payment,
    Registration,
    RegistrationOption,
    User,
)


class IsRegularUserFilter(SimpleListFilter):
    """
    Regular user custom combined filter
    """

    title = "is_regular_user"
    parameter_name = "is_regular_user"

    def lookups(self, request, model_admin):
        return (
            ("1", "Yes"),
            ("0", "No"),
        )

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(is_staff=False, is_superuser=False)
        if self.value() == "0":
            return queryset.filter(~Q(is_staff=False, is_superuser=False))


class UserAdmin(BaseUserAdmin):
    form = UserAdminForm

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "address")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    list_display = [
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_regular_user",
    ]
    list_filter = [IsRegularUserFilter]

    def is_regular_user(self, user):
        return not user.is_staff and not user.is_superuser

    is_regular_user.short_description = "Regular user"
    is_regular_user.boolean = True

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["username"].label = "Email (username)"
        return form

    #  # TODO: Show only regular users by default?
    #  def changelist_view(self, request, extra_context=None):
    #      ref = request.META.get('HTTP_REFERER', '')
    #      path = request.META.get('PATH_INFO', '')
    #      query = request.META.get('QUERY_STRING', '')
    #
    #      # TODO: Detect if there weren't other parameters for this page
    #      test = ref.split(path)[-1]
    #      ref_default = test and not test.startswith('?')
    #      is_default = not query
    #
    #      if is_default:
    #          q = request.GET.copy()
    #          q.setdefault('is_staff__exact', '0')
    #          return redirect('%s?%s' % (request.path, q.urlencode()))
    #
    #      return super(UserAdmin, self).changelist_view(
    #          request, extra_context=extra_context,
    #      )


#  admin.site.unregister(OriginalUser)  # It's not required here
admin.site.register(User, UserAdmin)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    date_hierarchy = "created_at"
    readonly_fields = ["emailed"]
    list_filter = ["event"]
    actions = ["email_registered_users"]

    @admin.action(description="Email message(s) to registered users")
    def email_registered_users(self, request, queryset):
        count = 0
        for obj in queryset:
            count += obj.send_email()
        self.message_user(
            request,
            f"Sent {queryset.count()} messages to {count} users",
            messages.SUCCESS,
        )


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "started",
        "until",
        #  "paid",
        "active",
        "membership_type",
    ]


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    readonly_fields = [
        "created_at",
        "updated_at",
    ]
    search_fields = [
        "event",
    ]
    list_display = [
        "user_column",
        "payment_column",
        "event",
        "option",
        "status",
        "created_at",
    ]
    list_filter = [
        "event", "payment__status", "status"
    ]
    actions = ["accept_user"]

    def user_column(self, reg):
        return reg.user.full_name_with_email

    user_column.short_description = "User"
    user_column.admin_order_field = "user"

    def payment_column(self, reg):
        print(reg.payment)
        return str(reg.payment) if reg.payment else "--"

    payment_column.short_description = "Payment"
    payment_column.admin_order_field = "payment"

    @admin.action(description="Accept user(s) and send acceptance email")
    def accept_user(self, request, queryset):
        for obj in queryset:
            obj.complete_registration()
        self.message_user(
            request,
            f"{queryset.count()} users accepted and emailed",
            messages.SUCCESS,
        )


@admin.register(RegistrationOption)
class RegistrationOptionAdmin(admin.ModelAdmin):
    form = RegistrationOptionAdminForm
    search_fields = [
        "item",
        #  'event',  # NOTE: Unsupported lookup 'icontains' for ForeignKey or join on the field not permitted.
    ]
    list_display = [
        "item",
        "event",
        "price",
        "currency",
    ]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    # TODO: Show linked options (in columns and in the form)?
    readonly_fields = [
        "registration_open",
        "url",
    ]
    search_fields = [
        "title",
    ]
    form = EventAdminForm
    list_display = [
        "title",
        "code",
        "active_registration_count",
        "max_participants",
        "registration_open",
        "registration_close",
        "public",
        "url",
    ]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    form = PaymentAdminForm
    # TODO: Improve
    readonly_fields = [
        "invoice_no",
        "created",
        "updated",
        "data",
    ]
    list_display = [
        "invoice_no",
        "status",
        "created",
        "updated",
    ]
    actions = ["mark_invoice_paid", "email_invoices", "email_receipts", "download_invoices", "download_receipts"]

    @admin.action(description="Mark selected invoices paid")
    def mark_invoice_paid(self, request, queryset):
        for obj in queryset:
            obj.mark_paid()
        self.message_user(
            request,
            f"{queryset.count()} invoices marked as paid",
            messages.SUCCESS,
        )

    @admin.action(description="Email unpaid invoices to user")
    def email_invoices(self, request, queryset):
        qs = queryset.filter(status__in=("CREATED", "ISSUED"))
        count = qs.count()

        if not count:
            self.message_user(
                request,
                "No unpaid invoices in queryset",
                messages.ERROR,
            )
            return

        for obj in qs:
            obj.email_invoice()

        self.message_user(
            request,
            f"{count} invoice(s) sent",
            messages.SUCCESS,
        )

    @admin.action(description="Download unpaid invoices")
    def download_invoices(self, request, queryset):
        qs = queryset.filter(status__in=("CREATED", "ISSUED"))

        if not qs.count():
            self.message_user(
                request,
                "No unpaid invoices in queryset",
                messages.ERROR,
            )
            return

        outfile = BytesIO()

        with zipfile.ZipFile(outfile, "w") as zf:
            for obj in qs:
                zf.writestr(f"DdS invoice {obj.invoice_no}.pdf", obj.invoice_pdf().output())

        response = HttpResponse(outfile.getvalue(), content_type="application/octet-stream")
        response["Content-Disposition"] = "attachment; filename=dds-invoices.zip"
        return response

    @admin.action(description="Email receipts for completed payments to user")
    def email_receipts(self, request, queryset):
        qs = queryset.filter(status="PAID")
        count = qs.count()

        if not count:
            self.message_user(
                request,
                "No completed payments in queryset",
                messages.ERROR,
            )
            return

        for obj in queryset:
            obj.email_receipt()
        self.message_user(
            request,
            f"{count} receipt(s) sent",
            messages.SUCCESS,
        )

    @admin.action(description="Download completed payment receipts")
    def download_receipts(self, request, queryset):
        qs = queryset.filter(status="PAID")

        if not qs.count():
            self.message_user(
                request,
                "No completed payments in queryset",
                messages.ERROR,
            )
            return

        outfile = BytesIO()

        with zipfile.ZipFile(outfile, "w") as zf:
            for obj in qs:
                zf.writestr(f"DdS receipt {obj.invoice_no}.pdf", obj.receipt_pdf().output())

        response = HttpResponse(outfile.getvalue(), content_type="application/octet-stream")
        response["Content-Disposition"] = "attachment; filename=dds-receipts.zip"
        return response
