from attr import s
from typing import Optional, List
from jstruct import JStruct, JList


@s(auto_attribs=True)
class AddressType:
    address1: Optional[str] = None
    address2: Optional[str] = None
    area: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    addresstype: Optional[str] = None
    country: Optional[str] = None
    postcode: Optional[int] = None


@s(auto_attribs=True)
class FromType:
    name: Optional[str] = None
    phonenumber: Optional[str] = None
    email: Optional[str] = None
    address: Optional[AddressType] = JStruct[AddressType]


@s(auto_attribs=True)
class TimeslotType:
    starttime: Optional[str] = None
    endtime: Optional[str] = None
    timezone: Optional[str] = None


@s(auto_attribs=True)
class DimensionsType:
    weight: Optional[float] = None


@s(auto_attribs=True)
class ItemType:
    itemdescription: Optional[str] = None
    quantity: Optional[int] = None
    isdangerousgood: Optional[bool] = None


@s(auto_attribs=True)
class ParcelJobType:
    ispickuprequired: Optional[bool] = None
    pickupaddressid: Optional[int] = None
    pickupservicetype: Optional[str] = None
    pickupservicelevel: Optional[str] = None
    pickupdate: Optional[str] = None
    pickuptimeslot: Optional[TimeslotType] = JStruct[TimeslotType]
    pickupinstructions: Optional[str] = None
    deliveryinstructions: Optional[str] = None
    deliverystartdate: Optional[str] = None
    deliverytimeslot: Optional[TimeslotType] = JStruct[TimeslotType]
    dimensions: Optional[DimensionsType] = JStruct[DimensionsType]
    items: List[ItemType] = JList[ItemType]


@s(auto_attribs=True)
class ReferenceType:
    merchantordernumber: Optional[str] = None


@s(auto_attribs=True)
class CreateShipmentRequestType:
    servicetype: Optional[str] = None
    servicelevel: Optional[str] = None
    requestedtrackingnumber: Optional[str] = None
    reference: Optional[ReferenceType] = JStruct[ReferenceType]
    createshipmentrequestfrom: Optional[FromType] = JStruct[FromType]
    to: Optional[FromType] = JStruct[FromType]
    parceljob: Optional[ParcelJobType] = JStruct[ParcelJobType]
