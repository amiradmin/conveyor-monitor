from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health),
    path("conveyors/", views.conveyors),
    path("vision/sources/", views.vision_sources),
    path("conveyors/<str:code>/", views.update_conveyor),
    path("conveyors/<str:code>/video/", views.conveyor_video),
    path("conveyors/<str:code>/status/", views.conveyor_status),
    path("conveyors/<str:code>/frame/", views.conveyor_frame),
    path("demo/status/", views.demo_status),
    path("telemetry/ingest/", views.ingest_telemetry),
    path("events/", views.events),
    path("events/<int:alarm_id>/evidence/", views.alarm_evidence),
    path("events/<int:alarm_id>/acknowledge/", views.acknowledge_alarm),
    path("events/<int:alarm_id>/capture-evidence/", views.recapture_alarm_evidence),
    path("control/stop/", views.controlled_stop),
]
