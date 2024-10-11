import json
from typing import List

from fastapi import WebSocket


class ChatServiceManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}
        self.mic_status: dict[int, bool] = {}
        self.qa_list: List[tuple[int, str]] = []

    async def connect(self, websocket: WebSocket, client_id: int):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.mic_status[client_id] = True

        self.send_personal_message(self._build_mic_status(), client_id)

    def disconnect(self, websocket: WebSocket, client_id: int):
        if client_id in self.active_connections:
            self.active_connections.pop(client_id)

        if client_id in self.mic_status:
            self.mic_status.pop(client_id)

    async def send_personal_message(self, message: str, client_id: int):
        await self.active_connections[client_id].send_text(message)

    async def broadcast(self, message: str):
        for client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

    def _build_mic_status(self) -> str:
        all_attendee_mic_status = [
            {"id": client_id, "type": "mic", "status": "on" if self.mic_status[client_id] else "off"} 
            for client_id in self.mic_status
        ]

        return json.dumps(all_attendee_mic_status)
    
    def end_meeting(self) -> None:
        for client_id in self.active_connections:
            self.disconnect(self.active_connections[client_id], client_id)
        
        self.qa_list.clear()
