from django.template.defaultfilters import register


@register.filter(name="getattr")
def getattr(obj, id):
    return obj[id] if type(obj) is dict and id in obj else ""
