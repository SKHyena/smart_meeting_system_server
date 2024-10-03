from typing import List

from pydantic import BaseModel

from .attendee import Attendee

class Reservation(BaseModel):    
    name: str
    time: str
    room: str
    subject: str
    topic: str

    attendees: List[Attendee]
