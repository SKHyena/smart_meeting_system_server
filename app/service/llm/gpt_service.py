import os
import json
from logging import Logger
from typing import List

from openai import OpenAI

from .prompt_generator import PromptGenerator
from ...model.utterance import Utterance

class GptServiceManager:
    
    def __init__(self, logger: Logger) -> None:
        self.logger = logger
        self._client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self._model = "gpt-4o"

    def _complete(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )

        if len(response.choices) == 0:
            return "Fail to summarize"
        
        return response.choices[0].message.content

    def summarize(self, utterances: List[Utterance]) -> str:
        dialogue: List[dict] = list(map(lambda x: x.model_dump(), utterances))    
        summarize_prompt = PromptGenerator.get_summarize_prompt(json.dumps(dialogue))
        return self._complete(summarize_prompt)
