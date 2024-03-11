from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .forms import (
    EventAdminForm,
    RegistrationOptionAdminForm,
    DiscountCodeAdminForm,
)

from .models import (
    Event,
    DiscountCode,
    GroupDiscount,
    Message,
    Registration,
    RegistrationOption,
    #  AppUser,
)


# Default registrations (without modifications)
admin.site.register(GroupDiscount)
admin.site.register(Message)


class UserAdmin(BaseUserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_active',
        'is_staff',
        #  'is_superuser',
    )


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class RegistrationAdmin(admin.ModelAdmin):
    # NOTE: Trying to show non-editable fields (this approach doesn't work)
    readonly_fields = ['created_at', 'updated_at']
    search_fields = [
        # TODO?
        #  'user',  # Unsupported lookup 'icontains' for ForeignKey or join on the field not permitted.
        #  'event',
        #  'options',  # Unsupported lookup 'icontains' for ForeignKey or join on the field not permitted.
    ]

    list_display = (
        'user_column',
        'event',
        'options_column',
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
    readonly_fields = ['created_at', 'updated_at']
    search_fields = [
        'title',
    ]
    form = EventAdminForm
    list_display = (
        'title',
        'code',
        'max_participants',
        'currency',
        'registration_close',
        'created_at',
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
