from google.cloud import translate



class TranslateService:

    def __init__(self, project_id: str):
        self._project_id = project_id        

    def translate(self, text: str, src: str, dest: str) -> str:
        return self._translate_text(text, src, dest)
    
    def translate(self, text: str, dest: str) -> str:
        return self._translate_text(text, None, dest)
    
    def _translate_text(
            self,
            text: str,
            src: str,
            dest: str
        ) -> str:

        client = translate.TranslationServiceClient()

        location = "global"
        parent = f"projects/{self._project_id}/locations/{location}"

        client.translate()

        response = client.translate_text(
            request={
                "parent": parent,
                "contents": [text],
                "mime_type": "text/plain",  # mime types: text/plain, text/html
                "source_language_code": src,
                "target_language_code": dest,
            }
        )

        if response is None or len(response.translations) == 0:
            raise RuntimeError("No translation found!")        
    
        return response.translations[0].translated_text
