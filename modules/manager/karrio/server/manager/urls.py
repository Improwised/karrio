"""
karrio server manager module urls
"""
from django.urls import include, path
from karrio.server.manager.views import router
from karrio.server.manager.views.trackers import TrackerWebhookListener

app_name = "karrio.server.manager"
urlpatterns = [
    path("v1/", include(router.urls)),
	path(
        "trackers/webhook",
        TrackerWebhookListener.as_view(),
        name="tracker-webhook",
    )
]
