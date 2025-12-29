"""URL configuration for called project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/

Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))

"""

from typing import NoReturn

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpRequest
from django.urls import include, path

admin.site.site_header = "Called"
admin.site.site_title = "Called administration"


def trigger_error(request: HttpRequest) -> NoReturn:  # noqa: ARG001
    """Trigger a test error to verify Sentry is working."""
    _division_by_zero = 1 / 0
    raise ValueError  # Unreachable, just for type checker.


urlpatterns = [  # noqa: RUF005
    path("admin/", admin.site.urls),
    path("board/", include("apps.board.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("sentry-test/", trigger_error),
    # For serving media files during development:
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
