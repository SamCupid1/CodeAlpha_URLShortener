from django.urls import path

from . import views

app_name = "shortener"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("shorten/", views.shorten, name="shorten"),
    path("delete/<str:code>/", views.delete_url, name="delete_url"),
    path("created/<str:code>/", views.created, name="created"),
    path("accounts/register/", views.register, name="register"),
    path("api/urls/", views.api_urls, name="api_urls"),
    path("api/urls/<str:code>/", views.api_url_detail, name="api_url_detail"),
    path("<str:code>/qr/", views.qr_code, name="qr_code"),
    path("<str:code>/", views.redirect_short_url, name="redirect"),
]
