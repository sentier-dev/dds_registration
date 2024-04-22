import re

from bs4 import BeautifulSoup
from django.conf import settings

# Single- and multi-line comments
re_comments = re.compile("<!--(.*?|(?:\n.*?)*?)-->", re.MULTILINE)


def BeautifulMiddleware(get_response):
    """
    Prettify html output middleware.
    """

    def middleware(request):
        response = get_response(request)
        # TODO: Do this conversion only in prod mode
        if not settings.DEV and response.status_code == 200 and response["content-type"].startswith("text/html"):
            content = response.content.decode("utf-8")
            # Remove comments
            content = re_comments.sub("", content)
            # Prettify
            beauty = BeautifulSoup(content, "html.parser")
            response.content = beauty.prettify()
        return response

    return middleware
