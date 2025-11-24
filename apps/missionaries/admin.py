from django.contrib import admin
from django.forms import ModelForm
from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import format_html

from .models import Missionary, Ward


@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    """Admin interface for Ward model."""

    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Missionary)
class MissionaryAdmin(admin.ModelAdmin):
    """Admin interface for Missionary model."""

    list_display = ("__str__", "type", "mission", "ward", "start_date", "end_date")
    list_filter = ("type", "ward", "mission")
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
                "fields": (
                    "type",
                    "ward",
                    "mission",
                    "start_date",
                    "end_date",
                    "photo",
                    "photo_edit_link",
                ),
            },
        ),
        (
            "Single Missionary",
            {
                "fields": ("first_name", "last_name"),
                "classes": ("collapse",),
            },
        ),
        (
            "Couple Missionaries",
            {
                "fields": (
                    "husband_first_name",
                    "husband_last_name",
                    "wife_first_name",
                    "wife_last_name",
                ),
                "classes": ("collapse",),
            },
        ),
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
            return format_html(
                '<a href="{}" target="_blank">Edit Photo</a>', url
            )
        return "Save missionary with a photo first"

    photo_edit_link.short_description = "Photo Editor"  # type: ignore[attr-defined]
