from attr import s
from typing import Optional, List
from jstruct import JList


@s(auto_attribs=True)
class EventType:
    shipperid: Optional[int] = None
    trackingnumber: Optional[str] = None
    shipperorderrefno: Optional[str] = None
    timestamp: Optional[str] = None
    status: Optional[str] = None
    isparcelonrtsleg: Optional[bool] = None
    comments: Optional[str] = None


@s(auto_attribs=True)
class TrackingResponseType:
    trackingnumber: Optional[str] = None
    isfullhistoryavailable: Optional[bool] = None
    events: List[EventType] = JList[EventType]
