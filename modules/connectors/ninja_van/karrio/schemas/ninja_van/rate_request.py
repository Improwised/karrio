from attr import s
from typing import Optional
from jstruct import JStruct


@s(auto_attribs=True)
class FromType:
    l1tiercode: Optional[str] = None
    l2tiercode: Optional[str] = None


@s(auto_attribs=True)
class RateRequestType:
    weight: Optional[int] = None
    servicelevel: Optional[str] = None
    raterequestfrom: Optional[FromType] = JStruct[FromType]
    to: Optional[FromType] = JStruct[FromType]
