import typing

import karrio.server.serializers as serializers
import karrio.server.providers.models as providers
from karrio.server.core.serializers import CARRIERS


CarrierName = str
CarrierSerializerType = typing.Type[serializers.ModelSerializer]


def generate_provider_serializer() -> typing.Dict[CarrierName, CarrierSerializerType]:
    def _create_serializer(name) -> CarrierSerializerType:
        class _CarrierSerializer(serializers.ModelSerializer):
            class Meta:
                model = providers.MODELS[name]
                exclude = ["id", "created_at", "updated_at", "created_by"]

        return _CarrierSerializer

    return {name: _create_serializer(name) for name in providers.MODELS.keys()}


SERIALIZERS = generate_provider_serializer()


class CarrierSerializer(serializers.Serializer):
    carrier_name = serializers.ChoiceField(
        required=True, choices=CARRIERS, help_text="Indicates a carrier (type)"
    )
    carrier_config = serializers.PlainDictField(
        required=True,
        help_text="the logistics service provider connection configuration",
    )

    def __init__(self, *args, **kwargs):
        carrier_name: str = kwargs.get("data", {}).get("carrier_name")
        instance, *_ = args + (None,)

        if carrier_name in SERIALIZERS:
            carrier_config_data: dict = kwargs.get("data", {}).get("carrier_config", {})
            serializer = SERIALIZERS[carrier_name]
            _args = (
                [providers.MODELS[carrier_name].objects.get(pk=carrier_config_data["id"])]
                if "id" in carrier_config_data
                else []
            )
            carrier_config = serializer.map(*_args, data=carrier_config_data).data
            kwargs.update(
                data=dict(carrier_name=carrier_name, carrier_config=carrier_config)
            )

            if "id" in carrier_config_data:
                args = _args

        super().__init__(*args, **kwargs)

    def create(self, validated_data: dict, **kwargs) -> providers.Carrier:
        created_by = validated_data["created_by"]
        carrier_name = validated_data["carrier_name"]
        carrier_config = {**validated_data["carrier_config"], "created_by": created_by}

        return providers.MODELS[carrier_name].objects.create(**carrier_config)

    def update(self, instance: providers.Carrier, validated_data: dict, **kwargs) -> providers.Carrier:
        carrier_config = validated_data["carrier_config"]

        for key, val in carrier_config.items():
            setattr(instance, key, val)

        instance.save()
        return instance

class ProofSerializer(serializers.Serializer):
    signature_uri = serializers.URLField(required=False)
    image_uris = serializers.ListField(
        child=serializers.URLField(), required=False
    )
    signed_by = serializers.DictField(required=False)

class ParcelMeasurementsSerializer(serializers.Serializer):
    weight = serializers.FloatField()
    dimensions = serializers.DictField()

class InternationalTransitSerializer(serializers.Serializer):
    state = serializers.CharField()
    remark = serializers.CharField(required=False)
    stage = serializers.CharField()
    linehaul_information = serializers.DictField(required=False)

class WebhookPayloadSerializer(serializers.Serializer):
    tracking_id = serializers.CharField()
    shipper_order_ref_no = serializers.CharField()
    timestamp = serializers.CharField()
    status = serializers.CharField()
    is_parcel_on_rts_leg = serializers.BooleanField()

    picked_up_information = serializers.DictField(required=False)
    arrived_at_pudo_information = serializers.DictField(required=False)
    pickup_exception = serializers.DictField(required=False)
    arrived_at_origin_hub_information = serializers.DictField(required=False)
    arrived_at_transit_hub_information = serializers.DictField(required=False)
    arrived_at_destination_hub_information = serializers.DictField(required=False)
    in_transit_to_next_sorting_hub_information = serializers.DictField(required=False)
    on_vehicle_information = serializers.DictField(required=False)
    parcel_measurements_information = ParcelMeasurementsSerializer(required=False)
    delivery_information = serializers.DictField(required=False)
    delivery_exception = serializers.DictField(required=False)
    rts_reason = serializers.CharField(required=False)
    cancellation_information = serializers.DictField(required=False)
    international_transit_information = InternationalTransitSerializer(required=False)
