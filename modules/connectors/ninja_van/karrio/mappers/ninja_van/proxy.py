"""Karrio Ninja Van client proxy."""

import karrio.lib as lib
import karrio.api.proxy as proxy
import karrio.mappers.ninja_van.settings as provider_settings


class Proxy(proxy.Proxy):
    settings: provider_settings.Settings

    def get_rates(self, request: lib.Serializable) -> lib.Deserializable[str]:
        response = lib.request(
            url=f"{self.settings.server_url}/{self.settings.country_code}/1.0/public/price",
            data=lib.to_json(request.serialize()),
            trace=self.trace_as("json"),
            method="POST",
             headers={
                "Accept": "application/json",
                "Content-type": "application/json",
                "Authorization": f"Bearer {self.settings.access_token}",
            },
        )

        return lib.Deserializable(response, lib.to_dict)

    def create_shipment(self, request: lib.Serializable) -> lib.Deserializable[str]:
        response = lib.request(
            url=f"{self.settings.server_url}/{self.settings.country_code}/4.2/orders",
            data=lib.to_json(request.serialize()),
            trace=self.trace_as("json"),
            method="POST",
             headers={
                "Accept": "application/json",
                "Content-type": "application/json",
                "Authorization": f"Bearer {self.settings.access_token}",
            },
        )

        return lib.Deserializable(response, lib.to_dict)

    def cancel_shipment(self, request: lib.Serializable) -> lib.Deserializable[str]:
        payload = request.serialize()
        tracking_numbers = payload.get('tracking_numbers', [])
        tracking_number = "&".join([f"tracking_number={tn}" for tn in tracking_numbers])
        response = lib.run_asynchronously(
            lambda payload: (
                payload["id"],
                lib.request(
                    url=f"{self.settings.server_url}/{self.settings.country_code}/2.2/orders/{tracking_number}",
                    trace=self.trace_as("json"),
                    method="DELETE",
                    headers={
                        "Accept": "application/json",
                        "Content-type": "application/json",
                        "Authorization": f"Bearer {self.settings.access_token}",
                    },
                ),
            ),
            payload,
        )

        return lib.Deserializable(
            response,
            lambda __: [(id, lib.to_dict(_)) for id, _ in __],
        )

    def get_tracking(self, request: lib.Serializable) -> lib.Deserializable[str]:
        payload = request.serialize()
        tracking_numbers = payload.get('tracking_numbers', [])
        tracking_number = "&".join([f"tracking_number={tn}" for tn in tracking_numbers])
        response = lib.request(
            url=f"{self.settings.server_url}/{self.settings.country_code}/1.0/orders/tracking-events/{tracking_number}",
            data=lib.to_json(request.serialize()),
            trace=self.trace_as("json"),
            method="GET",
                headers={
                    "Accept": "application/json",
                    "Content-type": "application/json",
                    "Authorization": f"Bearer {self.settings.access_token}",
                },
        )


        return lib.Deserializable(response, lib.to_dict)

    def get_waybill(self, request: lib.Serializable) -> lib.Deserializable[str]:
        payload = request.serialize()
        tracking_numbers = payload.get('tracking_numbers', [])
        tracking_number = "&".join([f"tracking_number={tn}" for tn in tracking_numbers])
        response = lib.request(
            url=f"{self.settings.server_url}/{self.settings.country_code}/2.0/reports/waybill/{tracking_number}",
            data=lib.to_json(request.serialize()),
            trace=self.trace_as("json"),
            method="GET",
                headers={
                    "Accept": "application/json",
                    "Content-type": "application/json",
                    "Authorization": f"Bearer {self.settings.access_token}",
                },
        )

        return lib.Deserializable(response, lib.to_dict)
