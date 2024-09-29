import os
import json
from logging import Logger
from typing import List

from openai import OpenAI

from .prompt_generator import PromptGenerator

class GptServiceManager:
    
    def __init__(self, logger: Logger) -> None:
        self.logger = logger
        self._client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self._model = "gpt-4o"
        self._categories = ["비자", "노무", "교육", "의료", "거주", "취업", "창업", "혼인", "법률"]

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

    def summarize(self, dialogue: List[dict]) -> str:
        summarize_prompt = PromptGenerator.get_summarize_prompt(json.dumps(dialogue))
        return self._complete(summarize_prompt)

    def categorize(self, dialogue: List[dict]) -> str:
        categorize_prompt = PromptGenerator.get_categorize_prompt(json.dumps(dialogue))
        categorize_completion = self._complete(categorize_prompt)
        return self._post_process_with_categorize(categorize_completion)
    
    def _post_process_with_categorize(self, completion: str) -> str:
        for category in self._categories:
            if category in completion:
                return category
        
        return "기타"
