from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import (
    Event,
    DiscountCode,
    GroupDiscount,
    Message,
    Registration,
    RegistrationOption,
    AppUser,
)


# Default registrations (without modifications)
admin.site.register(DiscountCode)
admin.site.register(GroupDiscount)
admin.site.register(Message)


# Define an inline admin descriptor for AppUser model which acts a bit like a singleton
class AppUserInline(admin.StackedInline):
    model = AppUser
    can_delete = False
    #  verbose_name_plural = "Users"


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = [AppUserInline]
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'get_email_verified',
        'is_staff',
    )

    def get_email_verified(self, user):
        return user.app_user.email_verified

    get_email_verified.short_description = 'Verified'
    get_email_verified.boolean = True

    def get_app_user(self, user):
        return user.app_user


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class RegistrationAdmin(admin.ModelAdmin):
    # NOTE: Trying to show non-editable fields (this approach doesn't work)
    readonly_fields = ['created_at', 'updated_at']
    #  search_fields = [
    #      # TODO?
    #      'user',
    #      'email',
    #      'event',
    #      'options',
    #  ]
    #  form = RegistrationAdminForm

    list_display = (
        #  'name_column',
        'user',  # 'user_column',
        'event',
        'options_column',
        'paid',
        'created_at',
    )

    def options_column(self, reg):
        return ', '.join([p.item for p in reg.options.all()])

    options_column.short_description = 'Options'
    options_column.admin_order_field = 'options'

    def name_column(self, obj):
        # NOTE: No data for user here!
        return str(obj)

    name_column.short_description = 'Name'
    #  name_column.admin_order_field = 'name'

    def user_column(self, reg):
        # TODO: We don't have user's data here for some reason. To find a way to get full user data to display it on the page
        #  user = User.objects.get(id=reg.user.id)
        #  return user.get_full_name()
        return reg.user

    user_column.short_description = 'User'
    user_column.admin_order_field = 'user'


admin.site.register(Registration, RegistrationAdmin)


class RegistrationOptionAdmin(admin.ModelAdmin):
    list_display = (
        'item',
        'price',
        'add_on',
        'event',
    )


admin.site.register(RegistrationOption, RegistrationOptionAdmin)


class EventAdmin(admin.ModelAdmin):
    # NOTE: Trying to show non-editable fields (this approach doesn't work)
    readonly_fields = ['created_at', 'updated_at']
    search_fields = [
        'title',
    ]
    #  form = EventAdminForm

    list_display = (
        'title',
        'code',
        'max_participants',
        'currency',
        'registration_close',
        'created_at',
    )


admin.site.register(Event, EventAdmin)


# from django.contrib import admin
# from .models import (
#     Event,
#     Session,
#     Choice,
#     Option,
#     Booking,
#     BookingOption,
#     Category,
# )
# from django.urls import reverse
# from django.utils.safestring import mark_safe
# from django.utils import timezone
# from django.contrib.admin.utils import unquote


# class EditLinkToInlineObjectMixin(object):
#     """
#     Mixin to allow having a link to the admin page of another Model
#     From http://stackoverflow.com/a/22113967
#     """

#     def edit_link(self, instance):
#         url = reverse(
#             "admin:%s_%s_change"
#             % (instance._meta.app_label, instance._meta.module_name),
#             args=[instance.pk],
#         )
#         if instance.pk:
#             return mark_safe('<a href="{u}">edit</a>'.format(u=url))
#         else:
#             return ""


# class LimitedAdminInlineMixin(object):
#     """
#     InlineAdmin mixin limiting the selection of related items according to
#     criteria which can depend on the current parent object being edited.

#     A typical use case would be selecting a subset of related items from
#     other inlines, ie. images, to have some relation to other inlines.

#     Use as follows::

#         class MyInline(LimitedAdminInlineMixin, admin.TabularInline):
#             def get_filters(self, obj):
#                 return (('<field_name>', dict(<filters>)),)

#     From https://gist.github.com/dokterbob/828117
#     """

#     @staticmethod
#     def limit_inline_choices(formset, field, empty=False, **filters):
#         """
#         This function fetches the queryset with available choices for a given
#         `field` and filters it based on the criteria specified in filters,
#         unless `empty=True`. In this case, no choices will be made available.
#         """
#         assert field in formset.form.base_fields

#         qs = formset.form.base_fields[field].queryset
#         if empty:
#             formset.form.base_fields[field].queryset = qs.none()
#         else:
#             qs = qs.filter(**filters)

#             formset.form.base_fields[field].queryset = qs

#     def get_formset(self, request, obj=None, **kwargs):
#         """
#         Make sure we can only select variations that relate to the current
#         item.
#         """
#         formset = super(LimitedAdminInlineMixin, self).get_formset(
#             request, obj, **kwargs
#         )

#         for (field, filters) in self.get_filters(obj):
#             if obj:
#                 self.limit_inline_choices(formset, field, **filters)
#             else:
#                 self.limit_inline_choices(formset, field, empty=True)

#         return formset

#     def get_filters(self, _):
#         """
#         Return filters for the specified fields. Filters should be in the
#         following format::

#             (('field_name', {'categories': obj}), ...)

#         For this to work, we should either override `get_filters` in a
#         subclass or define a `filters` property with the same syntax as this
#         one.
#         """
#         return getattr(self, "filters", ())


# class OptionInline(admin.TabularInline):
#     model = Option
#     fields = (
#         "title",
#         "default",
#     )


# class ChoiceAdmin(admin.ModelAdmin):
#     fields = (
#         "event",
#         "title",
#     )
#     readonly_fields = ("event",)
#     inlines = [OptionInline]
#     list_display = ("event", "title")


# class ChoiceInline(admin.TabularInline, EditLinkToInlineObjectMixin):
#     model = Choice
#     fields = (
#         "title",
#         "edit_link",
#     )
#     readonly_fields = ("edit_link",)


# class SessionInline(admin.TabularInline):
#     model = Session
#     fields = ("title", "start", "end", "max_participant")
#     extra = 1


# class CategoryInline(admin.TabularInline):
#     model = Category
#     fields = ("order", "name", "price", "groups1", "groups2")
#     extra = 1


# class EventAdmin(admin.ModelAdmin):
#     fields = (
#         ("title", "pub_status"),
#         ("start", "end"),
#         "timezone",
#         ("location_name", "location_address"),
#         ("owner", "organisers"),
#         ("booking_close", "choices_close"),
#         "max_participant",
#         "price_currency",
#     )
#     inlines = (
#         SessionInline,
#         CategoryInline,
#         ChoiceInline,
#     )
#     list_display = ("title", "timezone", "start_local", "end_local")

#     dt_format = "%a, %d %b %Y %H:%M:%S %Z"

#     def start_local(self, event):
#         """ Display the start datetime in its local timezone """
#         tz = event.timezone
#         dt = event.start.astimezone(tz)
#         return dt.strftime(self.dt_format)

#     def end_local(self, event):
#         """ Display the end datetime in its local timezone """
#         if event.end is None:
#             return None
#         tz = event.timezone
#         dt = event.end.astimezone(tz)
#         return dt.strftime(self.dt_format)

#     def add_view(self, request, form_url="", extra_context=None):
#         """
#         Override add view so we can peek at the timezone they've entered and
#         set the current timezone accordingly before the form is processed
#         """
#         if request.method == "POST":
#             tz_form = self.get_form(request)(request.POST)
#             if tz_form.is_valid():
#                 tz = tz_form.cleaned_data["timezone"]
#                 timezone.activate(tz)

#         return super(EventAdmin, self).add_view(request, form_url, extra_context)

#     def change_view(self, request, object_id, form_url="", extra_context=None):
#         """
#         Override change view so we can peek at the timezone they've entered and
#         set the current timezone accordingly before the form is processed
#         """
#         event = self.get_object(request, unquote(object_id))

#         if request.method == "POST":
#             tz_form = self.get_form(request, event)(request.POST, instance=event)
#             if tz_form.is_valid():
#                 tz = tz_form.cleaned_data["timezone"]
#                 timezone.activate(tz)
#         else:
#             timezone.activate(event.timezone)

#         return super(EventAdmin, self).change_view(
#             request, object_id, form_url, extra_context
#         )


# class BookingOptionInline(LimitedAdminInlineMixin, admin.TabularInline):
#     model = BookingOption

#     def get_filters(self, obj):
#         if obj:
#             return (("option", {"choice__event": obj.event}),)
#         return []


# class BookingAdmin(admin.ModelAdmin):
#     inlines = (BookingOptionInline,)
#     list_display = ("event", "person", "cancelledBy", "cancelledOn", "confirmedOn")
