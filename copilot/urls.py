from django.urls import path

from . import views

app_name = "copilot"

urlpatterns = [
    path("", views.panel, name="panel"),
    path("status", views.status, name="status"),
    path("search", views.search_view, name="search"),
    path("ask", views.ask_view, name="ask"),
    path("summarize", views.summarize_view, name="summarize"),
]
