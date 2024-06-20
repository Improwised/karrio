
import typing
import karrio.lib as lib
import karrio.core.units as units
import karrio.core.models as models
import karrio.providers.ninja_van.error as error
import karrio.providers.ninja_van.utils as provider_utils
import karrio.providers.ninja_van.units as provider_units
import karrio.schemas.ninja_van.create_shipment_request as ninja_van
import karrio.schemas.ninja_van.create_shipment_response as shipping


def parse_shipment_response(
    _responses: lib.Deserializable[dict],
    settings: provider_utils.Settings,
) -> typing.Tuple[typing.List[models.RateDetails], typing.List[models.Message]]:
    responses = _responses.deserialize()

    shipment = lib.to_multi_piece_shipment(
        [
            (
                f"{_}",
            (
        _extract_details(response, settings)
        if "tracking_number" in response
        else None
    ),
            )
            for _, response in enumerate(responses, start=1)
        ]
    )

    messages: typing.List[models.Message] = sum(
        [
            error.parse_error_response(response, settings)
            for response in responses
        ],
        start=[],
    )

    return shipment, messages


def _extract_details(
    data: typing.Tuple[dict, dict],
    settings: provider_utils.Settings,
) -> models.ShipmentDetails:
    details, label = data

    order: shipping.OrderResponseType = lib.to_object(
        shipping.OrderResponseType, details
    )

    return models.ShipmentDetails(
        carrier_id=settings.carrier_id,
        carrier_name=settings.carrier_name,
        tracking_number=order.tracking_number,
        shipment_identifier=order.requested_tracking_number,  # extract shipment identifier from shipment
        service_type=order.service_type
        items=[order.items],
        meta=dict(
            reference=order.reference,
            order_from=order.from,
            order_to=order.to,
            order_parcel_job=order.parcel_job,
            tracking_number=order.tracking_number,
        ),
    )


def shipment_request(
    payload: models.ShipmentRequest,
    settings: provider_utils.Settings,
) -> lib.Serializable:
    shipper = lib.to_address(payload.shipper)
    recipient = lib.to_address(payload.recipient)
    packages = lib.to_packages(payload.parcels)
    service = provider_units.ShippingService.map(payload.service).value_or_key
    options = lib.to_shipping_options(
        payload.options,
        package_options=packages.options,
    )

    # map data to convert karrio model to ninja_van specific type
    request = ninja_van.CreateShipmentRequestType(
        servicetype=service,
        servicelevel=options.service_level.state,
        requestedtrackingnumber=payload.reference,
        reference=ninja_van.ReferenceType(
            merchantordernumber=payload.reference
        ),
        createshipmentrequestfrom=ninja_van.FromType(
            name=shipper.person_name,
            phonenumber=shipper.phone,
            email=shipper.email,
            address=ninja_van.AddressType(
                address1=shipper.address_line1,
                address2=shipper.address_line2,
                area=shipper.city,
                city=shipper.city,
                state=shipper.state_code,
                country=shipper.country_code,
                postcode=shipper.postal_code,
            ),
        ),
        to=ninja_van.FromType(
            name=recipient.person_name,
            phonenumber=recipient.phone,
            email=recipient.email,
            address=ninja_van.AddressType(
                address1=recipient.address_line1,
                address2=recipient.address_line2,
                area=recipient.city,
                city=recipient.city,
                state=recipient.state_code,
                country=recipient.country_code,
                postcode=recipient.postal_code,
            ),
        ),
        parceljob=ninja_van.ParcelJobType(
            ispickuprequired=options.is_pickup_required.state,
            pickupaddressid=None,
            pickupservicetype=None,
            pickupservicelevel=None,
            pickupdate=options.pickup_date.state,
            pickuptimeslot=ninja_van.TimeslotType(
                starttime=options.pickup_start_time.state,
                endtime=options.pickup_end_time.state,
                timezone=options.pickup_timezone.state,
            ),
            pickupinstructions=options.pickup_instructions.state,
            deliveryinstructions=options.delivery_instructions.state,
            deliverystartdate=options.delivery_start_date.state,
            deliverytimeslot=ninja_van.TimeslotType(
                starttime=options.delivery_start_time.state,
                endtime=options.delivery_end_time.state,
                timezone=options.delivery_timezone.state,
            ),
            dimensions=ninja_van.DimensionsType(
                weight=packages.weight.KG,
            ),
            items=[
                ninja_van.ItemType(
                    itemdescription=item.description,
                    quantity=item.quantity,
                    isdangerousgood=item.is_dangerous_good,
                )
                for item in packages.items
            ],
        )
    )

    return lib.Serializable(request, lib.to_dict)
