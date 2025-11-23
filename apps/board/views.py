from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Case, F, Q, QuerySet, When
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from apps.missionaries.models import Missionary

PAGE_ITEM_COUNT = 6
DAYS_AFTER_END_DATE = 30  # Keep missionaries on the board for this long after end date.


@login_required
def index(request: HttpRequest) -> HttpResponse:
    """View for the main board page showing missionaries."""
    offset = int(request.GET.get("offset", 0))
    count, missionaries = _query_missionaries(offset)
    next_offset = offset + PAGE_ITEM_COUNT if offset + PAGE_ITEM_COUNT < count else 0
    context = {
        "missionaries": missionaries,
        "next_url": request.build_absolute_uri(f"?offset={next_offset}"),
    }
    template = "board/board.html" if missionaries else "board/empty.html"
    return render(request, template, context)


@login_required
def preview(request: HttpRequest) -> HttpResponse:
    """Preview a single missionary card."""
    missionary_id = request.GET.get("missionary_id")
    missionary = Missionary.objects.get(id=missionary_id)
    context = {
        "missionary": missionary,
    }
    return render(request, "board/preview.html", context)


def _query_missionaries(offset: int) -> tuple[int, QuerySet[Missionary]]:
    """Load missionaries from the database.

    :param offset: The offset for pagination.
    :return: A tuple containing the total count of active missionaries and a queryset of
        missionaries for the current page.
    """
    cutoff_date = date.today() - timedelta(days=DAYS_AFTER_END_DATE)  # noqa: DTZ011
    queryset = Missionary.objects.filter(Q(end_date__gte=cutoff_date)).order_by(
        Case(
            When(last_name="", then=F("husband_last_name")),
            default=F("last_name"),
        ),
        Case(
            When(first_name="", then=F("husband_first_name")),
            default=F("first_name"),
        ),
    )
    return queryset.count(), queryset[offset : offset + PAGE_ITEM_COUNT]
