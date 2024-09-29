from typing import List

from pydantic import BaseModel

from .utterance import Utterance

class Dialogue(BaseModel):
    dialogue: List[Utterance]
