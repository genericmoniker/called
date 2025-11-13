from django.contrib import admin
from django.forms import ModelForm
from django.http import HttpRequest

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
