from fastapi import WebSocket


class ChatServiceManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}
        self.client_locale: dict[int, str] = {}

    async def connect(self, websocket: WebSocket, client_id: int):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, websocket: WebSocket, client_id: int):
        if client_id in self.active_connections:
            self.active_connections.pop(client_id)
        
        if client_id in self.client_locale:
            self.client_locale.pop(client_id)

    async def send_personal_message(self, message: str, client_id: int):
        await self.active_connections[client_id].send_text(message)

    async def broadcast(self, message: str):
        for client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)
