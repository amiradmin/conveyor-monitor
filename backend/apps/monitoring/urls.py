from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health),
    path("conveyors/", views.conveyors),
    path("conveyors/<str:code>/status/", views.conveyor_status),
    path("demo/status/", views.demo_status),
    path("telemetry/ingest/", views.ingest_telemetry),
    path("events/", views.events),
    path("events/<int:alarm_id>/acknowledge/", views.acknowledge_alarm),
    path("control/stop/", views.controlled_stop),
]
