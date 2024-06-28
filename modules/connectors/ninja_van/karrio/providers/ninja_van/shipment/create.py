
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
    details = data

    order: shipping.OrderResponseType = lib.to_object(
        shipping.OrderResponseType, details
    )

    return models.ShipmentDetails(
        carrier_id=settings.carrier_id,
        carrier_name=settings.carrier_name,
        tracking_number=order.tracking_number,
        shipment_identifier=order.requested_tracking_number,  # extract shipment identifier from shipment
        service_type=order.service_type,
        items=[order.items],
        meta=dict(
            reference=order.reference,
            order_from=order.create_shipment_request_from,
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
    request = dict(
        service_type="Parcel",
        service_level=service,
        requested_tracking_number=payload.reference,
        reference=ninja_van.ReferenceType(
            merchant_order_number=payload.reference
        ),
        address_from=ninja_van.FromType(
            name=shipper.person_name,
            phone_number=shipper.phone_number,
            email=shipper.email,
            address=ninja_van.AddressType(
                address1=shipper.address_line1,
                address2=shipper.address_line2,
                area=shipper.city,
                city=shipper.city,
                state=shipper.state_code,
                country=shipper.country_code,
                post_code=shipper.postal_code,
            ),
        ),
        to=ninja_van.FromType(
            name=recipient.person_name,
            phone_number=recipient.phone_number,
            email=recipient.email,
            address=ninja_van.AddressType(
                address1=recipient.address_line1,
                address2=recipient.address_line2,
                area=recipient.city,
                city=recipient.city,
                state=recipient.state_code,
                country=recipient.country_code,
                post_code=recipient.postal_code,
            ),
        ),
        parcel_job=ninja_van.ParcelJobType(
            is_pickup_required=payload.metadata.get("is_pickup_required", False),
            pickup_addressid=None,
            pickup_service_type="Scheduled",
            pickup_service_level="Standard",
            pickup_date=payload.metadata.get("pickup_date", None),
            pickup_timeslot=ninja_van.TimeslotType(
                start_time=payload.metadata.get("pickup_timeslot", {}).get("start_time", None),
                end_time=payload.metadata.get("pickup_timeslot", {}).get("end_time", None),
                timezone=payload.metadata.get("pickup_timeslot", {}).get("timezone", None),
            ),
            pickup_instructions=options.pickup_instructions.state,
            delivery_instructions=options.delivery_instructions.state,
            delivery_startdate= payload.metadata.get("delivery_startdate", None),
            delivery_timeslot=ninja_van.TimeslotType(
                start_time=payload.metadata.get("delivery_timeslot", {}).get("start_time", None),
                end_time=payload.metadata.get("delivery_timeslot", {}).get("end_time", None),
                timezone=payload.metadata.get("delivery_timeslot", {}).get("timezone", None),
            ),
            dimensions=ninja_van.DimensionsType(
                weight=packages.weight.KG,
            ),
            items=[
                ninja_van.ItemType(
                    item_description=item.description,
                    quantity=item.quantity,
                    is_dangerous_good=payload.metadata.get("is_dangerous_good", False),
                )
                for item in packages.items
            ],
        )
    )

    # Custom serialization function
    def custom_serializer(_):
        serialized = lib.to_dict(_)
        if 'address_from' in serialized:
            serialized['from'] = serialized.pop('address_from')
        return serialized

    return lib.Serializable(request, custom_serializer)
