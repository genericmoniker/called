# Source - https://stackoverflow.com/a/18962676
# Posted by Charlesthk, modified by community. See post 'Timeline' for change history
# Retrieved 2025-11-09, License - CC BY-SA 4.0
# Modified to fit the project's needs.

from django import template
from django.forms import BoundField

register = template.Library()


@register.filter(name="add_class")
def add_class(value: BoundField, arg: str) -> str:
    """Add one or more CSS classes to a form field widget.

    Usage in template:

    {{ form.username|add_class:"input w-full" }}
    """
    return value.as_widget(attrs={"class": arg})
