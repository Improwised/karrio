import karrio.schemas.ninja_van.rate_request as ninja_van
import karrio.schemas.ninja_van.rate_response as rating
import typing
import karrio.lib as lib
import karrio.core.units as units
import karrio.core.models as models
import karrio.providers.ninja_van.error as error
import karrio.providers.ninja_van.utils as provider_utils
import karrio.providers.ninja_van.units as provider_units


def parse_rate_response(
    _response: lib.Deserializable[dict],
    settings: provider_utils.Settings,
) -> typing.Tuple[typing.List[models.RateDetails], typing.List[models.Message]]:
    response = _response.deserialize()
    messages = error.parse_error_response(response, settings)
    rates = [_extract_details(response.get("data"), settings)]

    return rates,messages


def _extract_details(
    data: dict,
    settings: provider_utils.Settings,
) -> models.RateDetails:

    rate = lib.to_object(rating.RateResponseType, data)
    total_charge = lib.to_money(rate.data.total_fee) if rate.data and rate.data.total_fee else 0.0

    return models.RateDetails(
        carrier_id=settings.carrier_id,
        carrier_name=settings.carrier_name,
        total_charge=total_charge,
        service="Standard",
    )


def rate_request(
    payload: models.RateRequest,
    settings: provider_utils.Settings,
) -> lib.Serializable:
    shipper = lib.to_address(payload.shipper)
    recipient = lib.to_address(payload.recipient)
    packages = lib.to_packages(payload.parcels)

    request = ninja_van.RateRequestType(
        weight=packages.weight.KG,
        service_level="Standard",
        rate_request_from=ninja_van.FromType(
            l1_tier_code=shipper.address_line1,
            l2_tier_code=shipper.address_line2,
        ),
        rate_request_to=ninja_van.FromType(
            l1_tier_code=recipient.address_line1,
            l2_tier_code=recipient.address_line2,
        )
    )

    return lib.Serializable(request, lib.to_dict)
