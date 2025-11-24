from django.urls import path

from . import views

app_name = "board"

urlpatterns = [
    path("", views.index, name="index"),
    path("preview/", views.preview, name="preview"),
    path("preview/save/", views.save_photo_transform, name="save_photo_transform"),
]
