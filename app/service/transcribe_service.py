import re
import logging

from google.cloud import speech


class TranscriptionService:

    def __init__(self, logger: logging) -> None:
        self.client = speech.SpeechClient()
        self.config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            sample_rate_hertz=44100,
            language_code="ko-KR",
        )
        self.streaming_config = speech.StreamingRecognitionConfig(
            config=self.config, interim_results=False
        )

        self.logger = logger
    
    def transcribe(self, bytes_arr: bytes) -> str:        
        self.logger.info(f"byte array : {bytes_arr}")
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

        for response in responses:
            each_result = response.results
            self.logger.info(f"each response result : {each_result}")
        #<google.api_core.grpc_helpers._StreamingResponseIterator
        speech.StreamingRecognizeResponse


        num_chars_printed = 0
        for response in responses:
            if not response.results:
                continue

            # The `results` list is consecutive. For streaming, we only care about
            # the first result being considered, since once it's `is_final`, it
            # moves on to considering the next utterance.
            result = response.results[0]
            if not result.alternatives:
                continue

            # Display the transcription of the top alternative.
            transcript = result.alternatives[0].transcript            
            self.logger.info(f"transcription result : {transcript}")

            # Display interim results, but with a carriage return at the end of the
            # line, so subsequent lines will overwrite them.
            #
            # If the previous result was longer than this one, we need to print
            # some extra spaces to overwrite the previous result
            overwrite_chars = " " * (num_chars_printed - len(transcript))

            if not result.is_final:                
                num_chars_printed = len(transcript)

            else:
                print(transcript + overwrite_chars)

                # Exit recognition if any of the transcribed phrases could be
                # one of our keywords.
                if re.search(r"\b(exit|quit)\b", transcript, re.I):
                    print("Exiting..")
                    break

                num_chars_printed = 0

        return transcript
