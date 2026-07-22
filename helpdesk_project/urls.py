from django.urls import include, path

from helpdesk import views as helpdesk_views

urlpatterns = [
    path("", helpdesk_views.home, name="home"),
    path("copilot/", include("copilot.urls")),
]
