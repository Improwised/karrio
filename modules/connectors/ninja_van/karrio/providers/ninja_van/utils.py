
import datetime
import karrio.core as core
import karrio.core.errors as errors
import karrio.lib as lib

class Settings(core.Settings):
    """Ninja Van connection settings."""

    client_id: str = None
    client_secret: str = None
    grant_type: str = "client_credentials"

    @property
    def carrier_name(self):
        return "ninja_van"

    @property
    def server_url(self):
        return (
            "https://api-sandbox.ninjavan.co"
            if self.test_mode
            else "https://api-sandbox.ninjavan.co" #"https://api.ninjavan.co" updATE later
        )

    @property
    def access_token(self):
        """Retrieve the access_token using the api_key|secret_key pair
        or collect it from the cache if an unexpired access_token exist.
        """
        if not all([self.client_id, self.client_secret, self.grant_type]):
            raise Exception(
                "The client_id, client_secret and grant_type are required for Rate, Ship and Other API requests."
            )

        cache_key = f"{self.carrier_name}|{self.client_id}|{self.client_secret}|{self.grant_type}"
        now = datetime.datetime.now() + datetime.timedelta(minutes=30)

        auth = self.connection_cache.get(cache_key) or {}
        token = auth.get("access_token")
        expiry = lib.to_date(auth.get("expiry"), current_format="%Y-%m-%d %H:%M:%S")

        if token is not None and expiry is not None and expiry > now:
            return token

        self.connection_cache.set(
            cache_key,
            lambda: login(
                self,
                client_id=self.client_id,
                client_secret=self.client_secret,
                grant_type=self.grant_type,
            ),
        )
        new_auth = self.connection_cache.get(cache_key)

        return new_auth["access_token"]


def login(settings: Settings, client_id: str = None, client_secret: str = None, grant_type: str = None):
    import karrio.providers.ninja_van.error as error
    result = lib.request(
        url=f"{settings.server_url}/{settings.account_country_code}/2.0/oauth/access_token",
        method="POST",
        headers={
            "content-Type": "application/json",
        },
        data=lib.to_json({"client_id": client_id, "client_secret": client_secret, "grant_type": grant_type}),
    )
    print ("====================================",client_id, "===", client_secret,settings.server_url, lib.to_dict(result) )
    response = lib.to_dict(result)
    messages = error.parse_error_response(response, settings)
    if any(messages):
        raise errors.ShippingSDKError(messages)
    expiry = datetime.datetime.now() + datetime.timedelta(
        seconds=float(response.get("expires_in", 0))
    )
    return {**response, "expiry": lib.fdatetime(expiry)}
