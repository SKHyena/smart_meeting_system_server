from pydantic import BaseModel


class Attendee(BaseModel):    
    name: str
    organization: str
    position: str
    email_address: str
    role: str
    email_delivery_status: bool


class Attendance(BaseModel):
    id: int
    connected_device: str
