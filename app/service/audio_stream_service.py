import json
from typing import List
from threading import Thread

from fastapi import WebSocket

from ..provider.audio_manager import ResumableMicrophoneSocketStream


class AudioStreamServiceManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}
        self.stream_status: dict[int, ResumableMicrophoneSocketStream] = {}
        self.stream_task: dict[int, Thread] = {}

    async def connect(self, websocket: WebSocket, client_id: int):
        await websocket.accept()        

    def disconnect(self, websocket: WebSocket, client_id: int):
        if client_id in self.active_connections:
            self.active_connections.pop(client_id)

        if client_id in self.stream_status:            
            self.stream_status[client_id].closed = True
            self.stream_status.pop(client_id)

    async def send_personal_message(self, message: str, client_id: int):
        await self.active_connections[client_id].send_text(message)

    async def broadcast(self, message: str):
        for client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)    
