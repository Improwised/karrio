
import unittest
from unittest.mock import patch, ANY
from .fixture import gateway

import karrio
import karrio.lib as lib
import karrio.core.models as models


class TestNinjaVanRating(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.RateRequest = models.RateRequest(**RatePayload)

    def test_create_rate_request(self):
        request = gateway.mapper.create_rate_request(self.RateRequest)
        self.assertEqual(request.serialize(), RateRequest)

    def test_get_rate(self):
        with patch("karrio.mappers.ninja_van.proxy.lib.request") as mock:
            mock.return_value = RateResponse

    def test_parse_rate_response(self):
        with patch("karrio.mappers.ninja_van.proxy.lib.request") as mock:
            mock.return_value = RateResponse
            parsed_response = karrio.Rating.fetch(self.RateRequest).from_(gateway).parse()
            self.assertListEqual(lib.to_dict(parsed_response), ParsedRateResponse)

if __name__ == "__main__":
    unittest.main()


RatePayload = {
    "shipper": {
        "company_name": "ninja_van",
        "address_line1": "17 VULCAN RD",
        "city": "CANNING VALE",
        "postal_code": "6155",
        "country_code": "SG",
        "person_name": "TEST USER",
        "state_code": "WA",
        "email": "test@gmail.com",
        "phone_number": "(07) 3114 1499",
    },
    "recipient": {
        "company_name": "CGI",
        "address_line1": "23 jardin private",
        "city": "Ottawa",
        "postal_code": "k1k 4t3",
        "country_code": "CA",
        "person_name": "Jain",
        "state_code": "ON",
    },
    "parcels": [
        {
            "height": 50,
            "length": 50,
            "weight": 20,
            "width": 12,
            "dimension_unit": "CM",
            "weight_unit": "KG",
        }
    ],
    "options": { },
    "reference": "REF-001",
}

ParsedRateResponse = [
   [{'carrier_id': 'ninja_van', 'carrier_name': 'ninja_van', 'currency': 'MYR', 'service': 'Standard', 'total_charge': 0.0}], []
]


RateRequest = {
   "rate_request_from": {'l1_tier_code': '17 VULCAN RD'},
   "rate_request_to": {'l1_tier_code': '23 jardin private'},
   "service_level": 'Standard',
   "weight": 20.0
}

RateResponse = """{
    "data": {
    "total_fee": 90000
    }
}
"""
