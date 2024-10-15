import re
import logging
from typing import List

from google.cloud import speech


class TranscriptionService:

    def __init__(self, logger: logging) -> None:
        self.client = speech.SpeechClient()
        self.config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="ko-KR",
        )
        self.streaming_config = speech.StreamingRecognitionConfig(
            config=self.config, interim_results=True
        )

        self.logger = logger
    
    def transcribe(self, bytes_arr: bytes) -> List[str]:        
        self.logger.info(f"length of bytes : {len(bytes_arr)}")
        contents = [bytes_arr]        
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content) for content in contents
        )

        responses = self.client.streaming_recognize(self.streaming_config, requests)
        return self._listen_print_loop(responses)

    def _listen_print_loop(self, responses: object) -> List[str]:
        transcript = ""
        self.logger.info(f"transcription response : {responses}")

        response_list = list(responses)
        self.logger.info(f"transcription response length : {len(response_list)}")

        transcriptions = []        

        for response in response_list:
            if not response.results:
                continue

            result = response.results[0]
            transcript = result.alternatives[0].transcript

            if result.is_final:
                self.logger.info(f"final text : {transcript}")
                transcriptions.append(f"final text : {transcript}")
                
            else:
                self.logger.info(f"transient text : {transcript}")
                transcriptions.append(f"transient text : {transcript}")

        return transcriptions
