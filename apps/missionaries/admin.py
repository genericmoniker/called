from datetime import date
from typing import override

from django.contrib import admin
from django.db.models import Case, F, Q, QuerySet, When
from django.forms import ModelForm
from django.http import HttpRequest
from django.template.response import TemplateResponse
from django.urls import URLPattern, path, reverse
from django.utils.html import format_html

from .models import Missionary, Ward


@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    """Admin interface for Ward model."""

    list_display = ("name",)
    search_fields = ("name",)


class CurrentlyServingFilter(admin.SimpleListFilter):
    """Filter missionaries by whether they are currently serving."""

    title = "serving status"
    parameter_name = "serving"

    @override
    def lookups(
        self, request: HttpRequest, model_admin: admin.ModelAdmin
    ) -> list[tuple[str, str]]:
        """Return filter choices."""
        return [
            ("yes", "Currently serving"),
            ("no", "Not currently serving"),
        ]

    @override
    def queryset(
        self, request: HttpRequest, queryset: QuerySet[Missionary]
    ) -> QuerySet[Missionary]:
        """Apply the filter to the queryset."""
        today = date.today()  # noqa: DTZ011
        if self.value() == "yes":
            return queryset.filter(start_date__lte=today, end_date__gte=today)
        if self.value() == "no":
            return queryset.exclude(start_date__lte=today, end_date__gte=today)
        return queryset


class MissingPhotoFilter(admin.SimpleListFilter):
    """Filter missionaries by whether they have a photo uploaded."""

    title = "photo"
    parameter_name = "has_photo"

    @override
    def lookups(
        self, request: HttpRequest, model_admin: admin.ModelAdmin
    ) -> list[tuple[str, str]]:
        """Return filter choices."""
        return [
            ("no", "Missing photo"),
            ("yes", "Has photo"),
        ]

    @override
    def queryset(
        self, request: HttpRequest, queryset: QuerySet[Missionary]
    ) -> QuerySet[Missionary]:
        """Apply the filter to the queryset."""
        if self.value() == "no":
            return queryset.filter(Q(photo__isnull=True) | Q(photo=""))
        if self.value() == "yes":
            return queryset.exclude(Q(photo__isnull=True) | Q(photo=""))
        return queryset


@admin.register(Missionary)
class MissionaryAdmin(admin.ModelAdmin):
    """Admin interface for Missionary model."""

    list_display = ("__str__", "type", "mission", "ward", "start_date", "end_date")
    list_filter = (
        CurrentlyServingFilter,
        MissingPhotoFilter,
        "type",
        "ward",
        "mission",
    )
    search_fields = (
        "first_name",
        "last_name",
        "husband_first_name",
        "husband_last_name",
        "wife_first_name",
        "wife_last_name",
        "mission",
    )
    readonly_fields = ("photo_edit_link",)
    fieldsets = (
        (
            None,
            {
                "fields": ("type",),
            },
        ),
        (
            "Name (Single Missionary)",
            {
                "fields": ("first_name", "last_name"),
            },
        ),
        (
            "Name (Couple Missionaries)",
            {
                "fields": (
                    "husband_first_name",
                    "husband_last_name",
                    "wife_first_name",
                    "wife_last_name",
                ),
            },
        ),
        (
            "Details",
            {
                "fields": (
                    "ward",
                    "mission",
                    "start_date",
                    "end_date",
                    "photo",
                    "photo_edit_link",
                ),
            },
        ),
    )

    def get_urls(self) -> list[URLPattern]:
        """Prepend the missing photos report URL to the default admin URLs."""
        custom_urls = [
            path(
                "missing-photos/",
                self.admin_site.admin_view(self.missing_photos_report),
                name="missionaries_missionary_missing_photos",
            ),
        ]
        return custom_urls + super().get_urls()

    def missing_photos_report(self, request: HttpRequest) -> TemplateResponse:
        """Render a report of currently serving missionaries without photos."""
        today = date.today()  # noqa: DTZ011
        missionaries = (
            Missionary.objects.filter(start_date__lte=today, end_date__gte=today)
            .filter(Q(photo__isnull=True) | Q(photo=""))
            .order_by(
                Case(
                    When(last_name="", then=F("husband_last_name")),
                    default=F("last_name"),
                ),
                Case(
                    When(first_name="", then=F("husband_first_name")),
                    default=F("first_name"),
                ),
            )
        )
        context = {
            **self.admin_site.each_context(request),
            "title": "Missing Photos Report",
            "opts": self.model._meta,  # noqa: SLF001
            "missionaries": missionaries,
            "count": missionaries.count(),
        }
        return TemplateResponse(
            request,
            "admin/missionaries/missionary/missing_photos_report.html",
            context,
        )

    def save_model(
        self,
        request: HttpRequest,
        obj: Missionary,
        form: ModelForm,
        change: bool,  # noqa: FBT001
    ) -> None:
        """Save the Missionary model instance."""
        # Set the created_by field on creation to the current user.
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def photo_edit_link(self, obj: Missionary) -> str:
        """Display a link to edit the photo positioning."""
        if obj.pk and obj.photo:
            url = reverse("board:preview") + f"?missionary_id={obj.pk}&edit=1"
            return format_html('<a href="{}" target="_blank">Edit Photo</a>', url)
        return "Save missionary with a photo first"

    photo_edit_link.short_description = "Photo Editor"  # type: ignore[attr-defined]
