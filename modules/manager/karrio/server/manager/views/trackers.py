import io
import base64
import logging
import django_downloadview

from django.db.models import Q
from django.urls import path, re_path
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.pagination import LimitOffsetPagination
from django.core.files.base import ContentFile
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status

from django.utils import timezone
from karrio.server.core.views.api import GenericAPIView, APIView
from karrio.server.manager.router import router
import karrio.server.manager.serializers as serializers
import karrio.server.core.dataunits as dataunits
import karrio.server.manager.models as models
import karrio.server.core.filters as filters
import karrio.server.openapi as openapi
import requests

ENDPOINT_ID = "$$$$$$"  # This endpoint id is used to make operation ids unique make sure not to duplicate
logger = logging.getLogger(__name__)
Trackers = serializers.PaginatedResult("TrackerList", serializers.TrackingStatus)


class TrackerList(GenericAPIView):
    throttle_scope = "carrier_request"
    pagination_class = type(
        "CustomPagination", (LimitOffsetPagination,), dict(default_limit=20)
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = filters.TrackerFilters
    serializer_class = Trackers
    model = models.Tracking

    def get_queryset(self):
        queryset = super().get_queryset()
        _filters = tuple()
        query_params = getattr(self.request, "query_params", {})
        carrier_name = query_params.get("carrier_name")

        if carrier_name is not None:
            _filters += (
                Q(
                    **{
                        f"tracking_carrier__{carrier_name.replace('_', '')}settings__isnull": False
                    }
                ),
            )

        return queryset.filter(*_filters)

    @openapi.extend_schema(
        tags=["Trackers"],
        operation_id=f"{ENDPOINT_ID}list",
        extensions={"x-operationId": "listTrackers"},
        summary="List all package trackers",
        parameters=filters.TrackerFilters.parameters,
        responses={
            200: Trackers(),
            404: serializers.ErrorResponse(),
            500: serializers.ErrorResponse(),
        },
    )
    def get(self, request: Request):
        """
        Retrieve all shipment trackers.
        """
        trackers = self.filter_queryset(self.get_queryset())
        response = self.paginate_queryset(
            serializers.TrackingStatus(trackers, many=True).data
        )
        return self.get_paginated_response(response)

    @openapi.extend_schema(
        tags=["Trackers"],
        operation_id=f"{ENDPOINT_ID}add",
        extensions={"x-operationId": "addTracker"},
        summary="Add a package tracker",
        request=serializers.TrackingData(),
        responses={
            200: serializers.TrackingStatus(),
            400: serializers.ErrorResponse(),
            424: serializers.ErrorMessages(),
            500: serializers.ErrorResponse(),
        },
        parameters=[
            openapi.OpenApiParameter(
                "hub",
                location=openapi.OpenApiParameter.QUERY,
                type=openapi.OpenApiTypes.STR,
                required=False,
            ),
            openapi.OpenApiParameter(
                "pending_pickup",
                location=openapi.OpenApiParameter.QUERY,
                type=openapi.OpenApiTypes.BOOL,
                required=False,
                description=(
                    "Add this flag to add the tracker whether the tracking info exist or not."
                    "When the package is eventually picked up, the tracker with capture real time updates."
                ),
            ),
        ],
    )
    def post(self, request: Request):
        """
        This API creates or retrieves (if existent) a tracking status object containing the
        details and events of a shipping in progress.
        """
        query = request.query_params
        serializer = serializers.TrackingData(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        carrier_name = query.get("hub") if "hub" in query else data["carrier_name"]
        pending_pickup = serializers.get_query_flag(
            "pending_pickup", query, nullable=False
        )

        instance = (
            models.Tracking.access_by(request)
            .filter(
                **{
                    "tracking_number": data["tracking_number"],
                    f"tracking_carrier__{carrier_name.replace('_', '')}settings__isnull": False,
                }
            )
            .first()
        )

        carrier_filter = {
            **{k: v for k, v in query.items() if k != "hub"},
            # If a hub is specified, use the hub as carrier to track the package
            "carrier_name": carrier_name,
        }
        data = {
            **data,
            "tracking_number": data["tracking_number"],
            "options": (
                {data["tracking_number"]: {"carrier": data["carrier_name"]}}
                if "hub" in query
                else {}
            ),
        }

        tracker = (
            serializers.TrackingSerializer.map(instance, data=data, context=request)
            .save(carrier_filter=carrier_filter, pending_pickup=pending_pickup)
            .instance
        )

        return Response(
            serializers.TrackingStatus(tracker).data,
            status=status.HTTP_202_ACCEPTED,
        )


class TrackersCreate(APIView):
    throttle_scope = "carrier_request"

    @openapi.extend_schema(
        tags=["Trackers"],
        operation_id=f"{ENDPOINT_ID}create",
        extensions={"x-operationId": "createTracker"},
        summary="Create a package tracker",
        deprecated=True,
        responses={
            200: serializers.TrackingStatus(),
            400: serializers.ErrorResponse(),
            424: serializers.ErrorMessages(),
            500: serializers.ErrorResponse(),
        },
        parameters=[
            openapi.OpenApiParameter(
                "tracking_number",
                location=openapi.OpenApiParameter.PATH,
                type=openapi.OpenApiTypes.STR,
                required=True,
            ),
            openapi.OpenApiParameter(
                "carrier_name",
                location=openapi.OpenApiParameter.QUERY,
                type=openapi.OpenApiTypes.STR,
                enum=dataunits.NON_HUBS_CARRIERS,
                required=True,
            ),
            openapi.OpenApiParameter(
                "hub",
                location=openapi.OpenApiParameter.QUERY,
                type=openapi.OpenApiTypes.STR,
                required=False,
            ),
        ],
        request=None,
    )
    def get(self, request: Request, carrier_name: str, tracking_number: str):
        """
        This API creates or retrieves (if existent) a tracking status object containing the
        details and events of a shipping in progress.
        """
        instance = (
            models.Tracking.access_by(request)
            .filter(tracking_number=tracking_number)
            .first()
        )

        query = request.query_params
        carrier_filter = {
            **{k: v for k, v in query.items() if k != "hub"},
            # If a hub is specified, use the hub as carrier to track the package
            "carrier_name": (query.get("hub") if "hub" in query else carrier_name),
        }
        data = {
            "tracking_number": tracking_number,
            "options": (
                {tracking_number: {"carrier": carrier_name}} if "hub" in query else {}
            ),
        }

        tracker = (
            serializers.TrackingSerializer.map(instance, data=data, context=request)
            .save(carrier_filter=carrier_filter, pending_pickup=False)
            .instance
        )

        return Response(
            serializers.TrackingStatus(tracker).data,
            status=status.HTTP_202_ACCEPTED,
        )


class TrackersDetails(APIView):
    throttle_scope = "carrier_request"
    permission_classes = [IsAuthenticatedOrReadOnly]

    @openapi.extend_schema(
        tags=["Trackers"],
        operation_id=f"{ENDPOINT_ID}retrieve",
        extensions={"x-operationId": "retrieveTracker"},
        summary="Retrieves a package tracker",
        responses={
            200: serializers.TrackingStatus(),
            404: serializers.ErrorMessages(),
            500: serializers.ErrorResponse(),
        },
    )
    def get(self, request: Request, id_or_tracking_number: str):
        """
        Retrieve a package tracker
        """
        __filter = Q(pk=id_or_tracking_number) | Q(
            tracking_number=id_or_tracking_number
        )
        trackers = models.Tracking.objects.filter(__filter)

        if len(trackers) == 0:
            models.Tracking.objects.get(__filter)

        return Response(serializers.TrackingStatus(trackers.first()).data)

    @openapi.extend_schema(
        tags=["Trackers"],
        operation_id=f"{ENDPOINT_ID}update",
        extensions={"x-operationId": "updateTracker"},
        summary="Update tracker data",
        responses={
            200: serializers.TrackingStatus(),
            404: serializers.ErrorResponse(),
            400: serializers.ErrorResponse(),
            409: serializers.ErrorResponse(),
            500: serializers.ErrorResponse(),
        },
        request=serializers.TrackerUpdateData(),
    )
    def put(self, request: Request, id_or_tracking_number: str):
        tracker = models.Tracking.access_by(request).get(
            Q(pk=id_or_tracking_number) | Q(tracking_number=id_or_tracking_number)
        )
        serializers.can_mutate_tracker(tracker, update=True, payload=request.data)

        payload = serializers.TrackerUpdateData.map(data=request.data).data
        update = (
            serializers.TrackerUpdateData.map(
                tracker,
                context=request,
                data=serializers.process_dictionaries_mutations(
                    ["metadata", "options", "info"], payload, tracker
                ),
            )
            .save()
            .instance
        )

        return Response(serializers.TrackingStatus(update).data)

    @openapi.extend_schema(
        tags=["Trackers"],
        operation_id=f"{ENDPOINT_ID}remove",
        extensions={"x-operationId": "removeTracker"},
        summary="Discard a package tracker",
        responses={
            200: serializers.TrackingStatus(),
            404: serializers.ErrorResponse(),
            500: serializers.ErrorResponse(),
        },
    )
    def delete(self, request: Request, id_or_tracking_number: str):
        """
        Discard a package tracker.
        """
        tracker = models.Tracking.access_by(request).get(
            Q(pk=id_or_tracking_number) | Q(tracking_number=id_or_tracking_number)
        )

        tracker.delete(keep_parents=True)

        return Response(serializers.TrackingStatus(tracker).data)


class TrackerDocs(django_downloadview.VirtualDownloadView):
    @openapi.extend_schema(exclude=True)
    def get(
        self,
        request: Request,
        pk: str,
        doc: str = "delivery_image",
        **kwargs,
    ):
        """Retrieve a tracker image."""
        self.tracker = models.Tracker.objects.get(pk=pk)
        self.image = getattr(self.tracker, doc)
        self.name = f"{doc}_{self.tracker.tracking_number}"

        query_params = request.GET.dict()
        self.preview = "preview" in query_params
        self.attachment = "download" in query_params

        response = super(TrackerDocs, self).get(request, pk, doc, format, **kwargs)
        response["X-Frame-Options"] = "ALLOWALL"
        return response

    def get_file(self):
        content = base64.b64decode(self.image or "")
        buffer = io.BytesIO()
        buffer.write(content)

        return ContentFile(buffer.getvalue(), name=self.name)

class TrackerWebhookListener(APIView):
    throttle_scope = "carrier_request"

    def post(self, request: Request):
        """
        Receive and process tracker status updates from carrier webhooks.
        """
        print("Received webhook payload:============", request.data)  # Debug log

        serializer = serializers.WebhookPayload(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid payload", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        print("Serializer:============", serializer.validated_data.get('tracking_id'))  # Debug log

        try:
            tracker = models.Tracking.access_by(request).get(
                Q(tracking_number=serializer.validated_data.get('tracking_id'))
            )

            # get me the carrier name from the tracker
            carrier_id = tracker.tracking_carrier_id
            carrier_name = tracker.carrier_name
            print("Carrier Name:============", carrier_id)  # Debug log
            print("Carrier Settings:============", carrier_name)  # Debug log

            # If carrier name is ninja_van then make the post request post
            if carrier_name == "ninja_van":
                tracking_number = serializer.validated_data.get('tracking_id')
                new_status = serializer.validated_data.get('status')
                timestamp = serializer.validated_data.get('timestamp')
                shipper_order_ref_number = serializer.validated_data.get('shipper_order_ref_no')
                tracker.status = new_status
                tracker.reference = shipper_order_ref_number
                tracker.updated_at = timezone.now()
                tracker.save()
                forward_url = "http://nifi/ninjavan/webhook"
                response = requests.post(forward_url, json=request.data)
                if response.status_code == 200:
                    return Response({"status": "received"}, status=status.HTTP_200_OK)
                else:
                    return Response({"status": "error", "message": "Failed to forward data"}, status=status.HTTP_400_BAD_REQUEST)
            if carrier_name == "jne":
                tracking_number = serializer.validated_data.get('tracking_id')
                new_status = serializer.validated_data.get('status')
                timestamp = serializer.validated_data.get('timestamp')
                shipper_order_ref_number = serializer.validated_data.get('shipper_order_ref_no')
                tracker.status = new_status
                tracker.reference = shipper_order_ref_number
                tracker.updated_at = timezone.now()
                tracker.save()
                forward_url = "http://nifi/jne/webhook"
                response = requests.post(forward_url, json=request.data)
                if response.status_code == 200:
                    return Response({"status": "received"}, status=status.HTTP_200_OK)
                else:
                    return Response({"status": "error", "message": "Failed to forward data"}, status=status.HTTP_400_BAD_REQUEST)

            print(f"Successfully updated tracker status for", tracking_number, " - " , new_status, " - " , timestamp, " - " , shipper_order_ref_number)  # Debug log
            return Response(
                {"message": "Webhook processed successfully"},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            print(f"Error processing webhook: {str(e)}")
            return Response(
                {"error": "Internal server error", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

router.urls.append(
    path(
        "trackers/webhook",
        TrackerWebhookListener.as_view(),
        name="tracker-webhook",
    )
)
router.urls.append(path("trackers", TrackerList.as_view(), name="trackers-list"))
router.urls.append(
    path(
        "trackers/<str:id_or_tracking_number>",
        TrackersDetails.as_view(),
        name="tracker-details",
    )
)
router.urls.append(
    path(
        "trackers/<str:carrier_name>/<str:tracking_number>",
        TrackersCreate.as_view(),
        name="shipment-tracker",
    )
)
router.urls.append(
    re_path(
        r"^trackers/(?P<pk>\w+)/(?P<doc>[a-z0-9]+)",
        TrackerDocs.as_view(),
        name="tracker-docs",
    )
)
