from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.renderers import JSONRenderer
from django.urls import path
from django.conf import settings

from karrio.server.conf import FEATURE_FLAGS
from karrio.server.core.router import router
import karrio.server.core.dataunits as dataunits
import karrio.server.openapi as openapi

ENDPOINT_ID = "&&"  # This endpoint id is used to make operation ids unique make sure not to duplicate
BASE_PATH = getattr(settings, "BASE_PATH", "")
<<<<<<< HEAD
References = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "VERSION": openapi.Schema(type=openapi.TYPE_STRING),
        "APP_NAME": openapi.Schema(type=openapi.TYPE_STRING),
        "APP_WEBSITE": openapi.Schema(type=openapi.TYPE_STRING),
        **{
            flag: openapi.Schema(type=openapi.TYPE_BOOLEAN)
            for flag in FEATURE_FLAGS
        },
        "ADMIN": openapi.Schema(type=openapi.TYPE_STRING),
        "OPENAPI": openapi.Schema(type=openapi.TYPE_STRING),
        "GRAPHQL": openapi.Schema(type=openapi.TYPE_STRING),

        "ADDRESS_AUTO_COMPLETE": openapi.Schema(type=openapi.TYPE_OBJECT),
        "countries": openapi.Schema(type=openapi.TYPE_OBJECT),
        "currencies": openapi.Schema(type=openapi.TYPE_OBJECT),
        "carriers": openapi.Schema(type=openapi.TYPE_OBJECT),
        "custom_carriers": openapi.Schema(type=openapi.TYPE_OBJECT),
        "customs_content_type": openapi.Schema(type=openapi.TYPE_OBJECT),
        "incoterms": openapi.Schema(type=openapi.TYPE_OBJECT),
        "states": openapi.Schema(type=openapi.TYPE_OBJECT),
        "services": openapi.Schema(type=openapi.TYPE_OBJECT),
        "service_names": openapi.Schema(type=openapi.TYPE_OBJECT),
        "options": openapi.Schema(type=openapi.TYPE_OBJECT),
        "option_names": openapi.Schema(type=openapi.TYPE_OBJECT),
        "package_presets": openapi.Schema(type=openapi.TYPE_OBJECT),
        "packaging_types": openapi.Schema(type=openapi.TYPE_OBJECT),
        "payment_types": openapi.Schema(type=openapi.TYPE_OBJECT),
        "carrier_capabilities": openapi.Schema(type=openapi.TYPE_OBJECT),
        "service_levels": openapi.Schema(type=openapi.TYPE_OBJECT),
    },
=======
References = openapi.OpenApiResponse(
    openapi.OpenApiTypes.OBJECT,
    examples=[
        openapi.OpenApiExample(
            name="References",
            value={
                "VERSION": "",
                "APP_NAME": "",
                "APP_WEBSITE": "",
                **{
                    flag: True
                    for flag in FEATURE_FLAGS
                },
                "ADMIN": "",
                "OPENAPI": "",
                "GRAPHQL": "",
                "ADDRESS_AUTO_COMPLETE": {},
                "countries": {},
                "currencies": {},
                "carriers": {},
                "customs_content_type": {},
                "incoterms": {},
                "states": {},
                "services": {},
                "service_names": {},
                "options": {},
                "option_names": {},
                "package_presets": {},
                "packaging_types": {},
                "payment_types": {},
                "carrier_capabilities": {},
                "service_levels": {},
            }
        )
    ],
>>>>>>> c3e3097d ((replace) drf-yasg by drf-spectacular for OpenAPI v3 support)
)


@openapi.extend_schema(
    auth=[],
    methods=["get"],
    tags=["API"],
    operation_id=f"{ENDPOINT_ID}data",
    summary="Data References",
    responses={200: References},
)
@api_view(["GET"])
@permission_classes([AllowAny])
@renderer_classes([JSONRenderer])
def references(request: Request):
    try:
        return Response(dataunits.contextual_reference(), status=status.HTTP_200_OK)
    except Exception as e:
        import logging
        logging.exception(e)
        raise e


router.urls.append(path("references", references))
