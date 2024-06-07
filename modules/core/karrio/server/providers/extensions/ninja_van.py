import django.db.models as models
import karrio.server.providers.models as providers

@providers.has_auth_cache
class NinjaVanSettings(providers.Carrier):
   class Meta:
       db_table = "ninjavan_settings"
       verbose_name = "NinjaVan Settings"
       verbose_name_plural = "NinjaVan Settings"

       client_id = models.CharField(max_length=255, null=True, blank=True)
       client_secret = models.CharField(max_length=255, null=True, blank=True)
       grant_type = models.CharField(max_length=255, default="client_credentials")

   @property
   def carrier_name(self) -> str:
       return "ninja_van"

   def get_auth_data(self):
       return {
              "client_id": self.client_id,
              "client_secret": self.client_secret,
              "grant_type": self.grant_type,
       }

SETTINGS = NinjaVanSettings
