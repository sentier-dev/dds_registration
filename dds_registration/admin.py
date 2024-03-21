from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .forms import DiscountCodeAdminForm, EventAdminForm, RegistrationOptionAdminForm
from .models import (
    DiscountCode,
    Event,
    GroupDiscount,
    Message,
    Profile,
    Registration,
    RegistrationOption,
)

# Default registrations (without modifications)
admin.site.register(GroupDiscount)
admin.site.register(Message)


class ProfileInline(admin.StackedInline):
    model = Profile
    verbose_name_plural = 'Profile'


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_active',
        'is_staff',
    )

    def get_address(self):
        return self.profile.address


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class RegistrationAdmin(admin.ModelAdmin):
    # NOTE: Trying to show non-editable fields (this approach doesn't work)
    readonly_fields = ['invoice_no', 'created_at', 'updated_at']
    search_fields = [
        # TODO?
        #  'user',  # Unsupported lookup 'icontains' for ForeignKey or join on the field not permitted.
        #  'event',
        #  'options',  # Unsupported lookup 'icontains' for ForeignKey or join on the field not permitted.
    ]

    list_display = (
        'user_column',
        'invoice_name',
        'event',
        'payment_method',
        'options_column',
        'active',
        'paid',
        'created_at',
    )

    def user_column(self, reg):
        user = reg.user
        full_name = user.get_full_name()
        name = full_name if full_name else user.username
        if user.email:
            name += ' <{}>'.format(user.email)
        return name

    user_column.short_description = 'User'
    user_column.admin_order_field = 'user'

    def invoice_name(self, reg):
        return 'Invoice #{}'.format(reg.invoice_no)

    invoice_name.short_description = 'Invoice'
    invoice_name.admin_order_field = 'invoice_no'

    def options_column(self, reg):
        return ', '.join([p.item for p in reg.options.all()])

    options_column.short_description = 'Options'
    options_column.admin_order_field = 'options'


admin.site.register(Registration, RegistrationAdmin)


class RegistrationOptionAdmin(admin.ModelAdmin):
    form = RegistrationOptionAdminForm
    search_fields = [
        'item',
        #  'event',  # NOTE: Unsupported lookup 'icontains' for ForeignKey or join on the field not permitted.
    ]
    list_display = (
        'item',
        'price',
        'add_on',
        'event',
    )


admin.site.register(RegistrationOption, RegistrationOptionAdmin)


class EventAdmin(admin.ModelAdmin):
    # TODO: Show linked options (in columns and in the form)?
    readonly_fields = [
        'registration_open',
        'new_registration_full_url',
    ]
    search_fields = [
        'title',
    ]
    form = EventAdminForm
    list_display = (
        'title',
        'code',
        'max_participants',
        'currency',
        'registration_open',
        'registration_close',
        'public',
        'new_registration_full_url',
    )


admin.site.register(Event, EventAdmin)


class DiscountCodeAdmin(admin.ModelAdmin):
    form = DiscountCodeAdminForm
    list_display = (
        'event',
        'code',
        'percentage',
        'absolute',
    )


admin.site.register(DiscountCode, DiscountCodeAdmin)
