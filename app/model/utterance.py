from typing import Optional

from pydantic import BaseModel


class Utterance(BaseModel):
    timestamp: int | str
    speaker: str
    origin_text: str
    translated_text: Optional[str] = None
    locale: str
