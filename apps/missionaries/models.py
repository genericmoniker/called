from datetime import date
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class Ward(models.Model):
    """A missionary's home unit (ward)."""

    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name


def _upload_to_path(instance: models.Model, filename: str) -> str:
    """Generate an upload path for a missionary photo."""
    if not isinstance(instance, Missionary):
        msg = "Instance must be a Missionary"
        raise TypeError(msg)
    name = slugify(instance.full_name)
    original = Path(filename)
    ext = original.suffix
    return f"missionaries/photos/{name}{ext}"


class Missionary(models.Model):
    """A missionary (or missionary couple)."""

    MISSIONARY_TYPES = [
        ("elder", "Elder"),
        ("sister", "Sister"),
        ("couple", "Couple"),
    ]

    type = models.CharField(max_length=10, choices=MISSIONARY_TYPES)

    # Single missionaries
    first_name = models.CharField(max_length=100, blank=True, default="")
    last_name = models.CharField(max_length=100, blank=True, default="")

    # Couple missionaries
    husband_first_name = models.CharField(max_length=100, blank=True, default="")
    husband_last_name = models.CharField(max_length=100, blank=True, default="")
    wife_first_name = models.CharField(max_length=100, blank=True, default="")
    wife_last_name = models.CharField(max_length=100, blank=True, default="")

    mission = models.CharField(max_length=200)
    ward = models.ForeignKey(
        Ward,
        on_delete=models.CASCADE,
        related_name="missionaries",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    photo = models.ImageField(upload_to=_upload_to_path, blank=True, null=True)
    photo_scale = models.FloatField(default=1.0)
    photo_translate_x = models.IntegerField(default=0)
    photo_translate_y = models.IntegerField(default=0)

    # Metadata
    created_by = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:  # noqa: D106
        verbose_name_plural = "missionaries"

    def __str__(self) -> str:
        if self.type == "couple":
            return (
                f"Elder {self.husband_first_name} & "
                f"Sister {self.wife_first_name} {self.wife_last_name}"
            )
        if self.type == "elder":
            return f"Elder {self.first_name} {self.last_name}"
        return f"Sister {self.first_name} {self.last_name}"

    @property
    def full_name(self) -> str:
        """Get the full sortable name of the missionary."""
        if self.type == "couple":
            return (
                f"{self.husband_last_name} {self.husband_first_name} & "
                f"{self.wife_last_name} {self.wife_first_name}"
            )
        return f"{self.last_name} {self.first_name}"

    @property
    def photo_url(self) -> str:
        """Get the final photo URL, falling back to default images if none uploaded."""
        if self.photo and hasattr(self.photo, "url"):
            return self.photo.url
        if self.type == "elder":
            return "/static/img/elder.png"
        if self.type == "sister":
            return "/static/img/sister.png"
        return "/static/img/couple.png"

    @property
    def dates_serving(self) -> str:
        """Get the dates the missionary is serving."""
        return f"{_format_date(self.start_date)} - {_format_date(self.end_date)}"

    def clean(self) -> None:
        """Validate missionary data before saving."""
        if self.type == "couple":
            if not all(
                [
                    self.husband_first_name,
                    self.husband_last_name,
                    self.wife_first_name,
                    self.wife_last_name,
                ],
            ):
                raise ValidationError(  # noqa: TRY003
                    "Couple missionaries must have both husband and wife names.",
                )
        elif not all([self.first_name, self.last_name]):
            raise ValidationError(  # noqa: TRY003
                "Single missionaries must have first and last names.",
            )


def _format_date(date: date) -> str:
    """Format a date as 'Month Year', like 'January 2026'."""
    return date.strftime("%B %Y")
