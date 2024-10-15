import re
import logging

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
    
    def transcribe(self, bytes_arr: bytes) -> str:        
        self.logger.info(f"length of bytes : {len(bytes_arr)}")
        contents = [bytes_arr]        
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content) for content in contents
        )

        responses = self.client.streaming_recognize(self.streaming_config, requests)
        return self._listen_print_loop(responses)

    def _listen_print_loop(self, responses: object) -> str:
        """Iterates through server responses and prints them.

        The responses passed is a generator that will block until a response
        is provided by the server.

        Each response may contain multiple results, and each result may contain
        multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
        print only the transcription for the top alternative of the top result.

        In this case, responses are provided for interim results as well. If the
        response is an interim one, print a line feed at the end of it, to allow
        the next result to overwrite it, until the response is a final one. For the
        final one, print a newline to preserve the finalized transcription.

        Args:
            responses: List of server responses

        Returns:
            The transcribed text.
        """
        transcript = ""
        self.logger.info(f"transcription response : {responses}")

        response_list = list(responses)
        self.logger.info(f"transcription response length : {len(response_list)}")

        for response in response_list:
            if not response.results:
                continue

            result = response.results[0]
            transcript = result.alternatives[0].transcript

            if result.is_final:
                self.logger.info(f"final text : {transcript}")
                return f"final text : {transcript}"
                
            else:
                self.logger.info(f"transient text : {transcript}")
                return f"transient text : {transcript}"

        return transcript        
