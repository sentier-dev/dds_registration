from django.template.defaultfilters import register


@register.filter(name="is_in_list")
def is_in_list(value, list):
    return value in list
