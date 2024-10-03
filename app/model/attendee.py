from pydantic import BaseModel


class Attendee(BaseModel):    
    name: str
    group: str
    position: str
    email_address: str
    role: str
    email_delivery_status: bool
