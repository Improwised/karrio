"""
karrio server providers module urls
"""
from django.urls import include, path
from karrio.server.providers.views import router
from .views import test_ninjavan_webhook


app_name = 'karrio.server.providers'
urlpatterns = [
    path('v1/', include(router.urls)),
	path('webhook', test_ninjavan_webhook, name='test_ninjavan_webhook'),
]
