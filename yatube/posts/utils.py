from django.conf import settings
from django.core.paginator import Paginator

POST_PER_PAGE = getattr(settings, "POST_PER_PAGE", None)


def paginations(request, post_list):
    paginator = Paginator(post_list, POST_PER_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return page_obj
