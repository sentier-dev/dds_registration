# -*- coding:utf-8 -*-
from django.conf import settings


def common_values(request):
    data = {}
    data["settings"] = settings.PASS_VARIABLES
    return data
