"""Karrio Ninja Van client settings."""

import attr
import karrio.providers.ninja_van.utils as provider_utils


@attr.s(auto_attribs=True)
class Settings(provider_utils.Settings):
    """Ninja Van connection settings."""

    # required carrier specific properties
    client_id: str = None
    client_secret: str = None
    grant_type: str = "client_credentials"

    # generic properties
    id: str = None
    test_mode: bool = False
    carrier_id: str = "ninja_van"
    account_country_code: str = "SG"
    metadata: dict = {}
    config: dict = {}
