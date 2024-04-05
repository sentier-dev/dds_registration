from bs4 import BeautifulSoup
import re


# Single- and multi-line comments
re_comments = re.compile("<!--(.*?|(?:\n.*?)*?)-->", re.MULTILINE)


def BeautifulMiddleware(get_response):
    """
    Prettify html output middleware.
    """

    def middleware(request):
        response = get_response(request)
        if response.status_code == 200 and response["content-type"].startswith("text/html"):
            content = response.content.decode("utf-8")
            # Remove comments
            content = re_comments.sub("", content)
            # Prettify
            beauty = BeautifulSoup(content, "html.parser")
            response.content = beauty.prettify()
        return response

    return middleware
