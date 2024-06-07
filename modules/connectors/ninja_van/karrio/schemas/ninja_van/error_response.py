from attr import s
from typing import Optional, List
from jstruct import JList, JStruct


@s(auto_attribs=True)
class DetailType:
    reason: Optional[str] = None
    field: Optional[str] = None
    message: Optional[str] = None


@s(auto_attribs=True)
class ErrorType:
    code: Optional[str] = None
    requestid: Optional[str] = None
    title: Optional[str] = None
    message: Optional[str] = None
    details: List[DetailType] = JList[DetailType]


@s(auto_attribs=True)
class ErrorResponseType:
    error: Optional[ErrorType] = JStruct[ErrorType]
