from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health),
    path("conveyors/", views.conveyors),
    path("demo/status/", views.demo_status),
    path("control/stop/", views.controlled_stop),
]
