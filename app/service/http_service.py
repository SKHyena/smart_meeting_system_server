import requests


class HttpServiceManager:

    @staticmethod
    def post(url: str, header: dict, body: dict) -> dict:
        response = requests.post(url, headers=header, json=body)

        try:
            return response.json()
        except:        
            return {}
