from typing import List

from pydantic import BaseModel

from .attendee import Attendee

class Reservation(BaseModel):    
    name: str
    start_time: str
    end_time: str
    room: str
    subject: str
    topic: str

    attendees: List[Attendee]
