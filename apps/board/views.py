from datetime import date, timedelta
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.db.models import Case, F, Q, QuerySet, When
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from apps.missionaries.models import Missionary

PAGE_ITEM_COUNT = 6
DAYS_AFTER_END_DATE = 30  # Keep missionaries on the board for this long after end date.
MAX_PHOTO_SCALE = 3.0  # Maximum zoom level for photo editing


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


@login_required
@require_http_methods(["POST"])
def save_photo_transform(request: HttpRequest) -> JsonResponse:
    """Save photo transformation settings for a missionary.

    Expects POST data with:
    - missionary_id: ID of the missionary
    - photo_scale: Scale factor (>= 1.0)
    - photo_translate_x: X translation in pixels
    - photo_translate_y: Y translation in pixels
    """
    try:
        missionary_id = request.POST.get("missionary_id")
        if not missionary_id:
            return JsonResponse(
                {"success": False, "error": "Missing missionary_id"},
                status=400,
            )

        missionary = Missionary.objects.get(id=missionary_id)

        # Parse and validate transformation values
        try:
            scale = float(request.POST.get("photo_scale", 1.0))
            translate_x = int(request.POST.get("photo_translate_x", 0))
            translate_y = int(request.POST.get("photo_translate_y", 0))
        except (ValueError, TypeError) as e:
            return JsonResponse(
                {"success": False, "error": f"Invalid values: {e}"},
                status=400,
            )

        # Validate scale (minimum 1.0, maximum 3.0)
        if scale < 1.0 or scale > MAX_PHOTO_SCALE:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Scale must be between 1.0 and {MAX_PHOTO_SCALE}",
                },
                status=400,
            )

        # Update missionary
        missionary.photo_scale = scale
        missionary.photo_translate_x = translate_x
        missionary.photo_translate_y = translate_y
        missionary.save()

        return JsonResponse({"success": True})

    except Missionary.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Missionary not found"}, status=404
        )
    except Exception as e:  # noqa: BLE001
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def service_worker(_request: HttpRequest) -> HttpResponse:
    """Serve the service worker JavaScript file.

    Service workers need to be served from the same path or above the scope
    they control. We serve it from /board/service-worker.js so it can control
    the /board/ scope.
    """
    sw_path = Path(__file__).parent / "service-worker.js"
    content = sw_path.read_text()
    return HttpResponse(content, content_type="application/javascript")
