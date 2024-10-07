from typing import Optional

from pydantic import BaseModel


class Utterance(BaseModel):
    timestamp: int | str
    speaker: str
    text: str
