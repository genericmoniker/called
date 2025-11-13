from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from apps.missionaries.models import Missionary

PAGE_ITEM_COUNT = 6


@login_required
def index(request: HttpRequest) -> HttpResponse:
    """View for the main board page showing missionaries."""
    count = Missionary.objects.count()
    if count == 0:
        context = {
            "missionaries": [],
            "next_url": request.build_absolute_uri("?offset=0")
        }
        return render(request, "board/empty.html", context)

    offset = int(request.GET.get("offset", 0))
    next_offset = offset + PAGE_ITEM_COUNT if offset + PAGE_ITEM_COUNT < count else 0
    missionaries = Missionary.objects.all()[offset : offset + PAGE_ITEM_COUNT]
    context = {
        "missionaries": missionaries,
        "next_url": request.build_absolute_uri(f"?offset={next_offset}")
    }
    return render(request, "board/board.html", context)


def preview(request: HttpRequest) -> HttpResponse:
    """Preview a single missionary card."""
    missionary_id = request.GET.get("missionary_id")
    missionary = Missionary.objects.get(id=missionary_id)
    context = {
        "missionary": missionary,
    }
    return render(request, "board/preview.html", context)
