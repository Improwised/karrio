import io
import base64
import logging
import hmac
import hashlib
import json
from django.conf import settings
from rest_framework import status
from django.http import JsonResponse
from django.urls import path, re_path
from rest_framework.request import Request
from rest_framework.response import Response
from django.core.files.base import ContentFile
from django_downloadview import VirtualDownloadView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.decorators import api_view
from .serializers import WebhookPayloadSerializer
import requests

import karrio.server.openapi as openapi
import karrio.server.core.filters as filters
import karrio.server.providers.models as models
from karrio.server.core.gateway import Carriers
from karrio.server.providers.router import router
from karrio.server.core import datatypes, dataunits
from karrio.server.serializers import PaginatedResult
from karrio.server.core.views.api import GenericAPIView, APIView
from karrio.server.core.serializers import CarrierSettings, ErrorResponse

logger = logging.getLogger(__name__)
ENDPOINT_ID = "&&"  # This endpoint id is used to make operation ids unique make sure not to duplicate
CarriersSettingsList = PaginatedResult("CarrierList", CarrierSettings)


class CarrierList(GenericAPIView):
    pagination_class = LimitOffsetPagination
    default_limit = 100

    @openapi.extend_schema(
        tags=["Carriers"],
        operation_id=f"{ENDPOINT_ID}list",
        extensions={"x-operationId": "listCarriers"},
        summary="List all carriers",
        responses={
            200: CarriersSettingsList(),
            400: ErrorResponse(),
        },
        parameters=filters.CarrierFilters.parameters,
    )
    def get(self, request: Request):
        """Returns the list of configured carriers"""
        filter = {
            **filters.CarrierFilters(request.query_params).to_dict(),
            "context": request,
        }

        carriers = [carrier.data for carrier in Carriers.list(**filter)]
        response = self.paginate_queryset(CarrierSettings(carriers, many=True).data)
        return self.get_paginated_response(response)


class CarrierDetails(APIView):
    @openapi.extend_schema(
        tags=["Carriers"],
        operation_id=f"{ENDPOINT_ID}retrieve",
        extensions={"x-operationId": "retrieveCarrier"},
        summary="Retrieve a carrier account",
        responses={
            200: CarrierSettings(),
            404: ErrorResponse(),
        },
    )
    def get(self, request: Request, pk: str):
        """
        Retrieve a carrier account.
        """
        carrier = Carriers.list(request).get(pk=pk)
        return Response(CarrierSettings(carrier.data).data)


class CarrierServices(APIView):
    @openapi.extend_schema(
        tags=["Carriers"],
        operation_id=f"{ENDPOINT_ID}get_services",
        summary="Get carrier services",
        parameters=[
            openapi.OpenApiParameter(
                "carrier_name",
                location=openapi.OpenApiParameter.PATH,
                type=openapi.OpenApiTypes.STR,
                description=(
                    "The unique carrier slug. <br/>"
                    f"Values: {', '.join([f'`{c}`' for c in dataunits.CARRIER_NAMES])}"
                ),
            )
        ],
        responses={
            200: openapi.OpenApiTypes.OBJECT,
            404: ErrorResponse(),
            500: ErrorResponse(),
        },
    )
    def get(self, request: Request, carrier_name: str):
        """
        Retrieve a carrier's services
        """
        references = dataunits.contextual_reference()

        if carrier_name not in references["carriers"]:
            raise Exception(f"Unknown carrier: {carrier_name}")

        services = references["services"].get(carrier_name, {})

        return Response(services, status=status.HTTP_200_OK)


class CarrierLabelPreview(VirtualDownloadView):
    def get(
        self,
        request: Request,
        pk: str,
        format: str = "pdf",
        **kwargs,
    ):
        """
        Preview a carrier label template...
        """
        try:
            query_params = request.GET.dict()
            carrier = models.MODELS["generic"].objects.get(pk=pk)

            self.document = self._generate_label(carrier, format)
            self.name = f"{carrier.custom_carrier_name}_label.{format}"
            self.attachment = query_params.get("download", False)

            response = super(CarrierLabelPreview, self).get(
                request, pk, format, **kwargs
            )
            response["X-Frame-Options"] = "ALLOWALL"
            return response
        except Exception as e:
            return JsonResponse(dict(error=str(e)), status=status.HTTP_409_CONFLICT)

    def get_file(self):
        content = base64.b64decode(self.document or "")
        buffer = io.BytesIO()
        buffer.write(content)

        return ContentFile(buffer.getvalue(), name=self.name)

    def _generate_label(self, carrier, format):
        import karrio
        from karrio.core.utils import DP
        from karrio.providers.generic.units import SAMPLE_SHIPMENT_REQUEST

        template = carrier.label_template
        data = (
            template.shipment_sample
            if template is not None and len(template.shipment_sample.items()) > 0
            else SAMPLE_SHIPMENT_REQUEST
        )
        service = data.get("service") or next(
            (s.service_code for s in carrier.services)
        )
        request = DP.to_object(
            datatypes.ShipmentRequest,
            {
                **data,
                "service": service,
                "label_type": format.upper(),
                "selected_rate_id": data.get("selected_rate_id") or "",
                "rates": data.get("rates") or [],
            },
        )

        shipment, _ = karrio.Shipment.create(request).from_(carrier.gateway).parse()

        if shipment is None:
            raise Exception("Failed to generate label")

        return shipment.docs.label


router.urls.append(path("carriers", CarrierList.as_view(), name="carrier-list"))
router.urls.append(
    path("carriers/<str:pk>", CarrierDetails.as_view(), name="carrier-details")
)
router.urls.append(
    path(
        "carriers/<str:carrier_name>/services",
        CarrierServices.as_view(),
        name="carrier-services",
    )
)
if settings.CUSTOM_CARRIER_DEFINITION:
    router.urls.append(
        re_path(
            r"^carriers/(?P<pk>\w+)/label.(?P<format>[a-z0-9]+)",
            CarrierLabelPreview.as_view(),
            name="carrier-label",
        )
    )

@api_view(['POST'])
def test_ninjavan_webhook(request):
    serializer = WebhookPayloadSerializer(data=request.data)

    if serializer.is_valid():
        print("++++++++++++++++++++", serializer.validated_data)

        # Extract shipper_name from query parameters, with a default value
        shipper_name = request.GET.get('shipper_name', 'default_shipper')

        # Append shipper_name to the validated data payload
        payload_with_shipper = serializer.validated_data.copy()
        payload_with_shipper['shipper_name'] = shipper_name

        forward_url = 'http://127.0.0.1:5000/pos'
        response = requests.post(forward_url, json=payload_with_shipper)

        if response.status_code == 200:
            return Response({"status": "received"}, status=status.HTTP_200_OK)
        else:
            return Response({"status": "error", "message": "Failed to forward data"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
