import json
import os
import logging
import time
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .provider.database_manager import DatabaseManager
from .service.chat_service import ChatServiceManager
from .service.llm.gpt_service import GptServiceManager
from .model.reservation import Reservation


app = FastAPI()
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)

db_manager = DatabaseManager(
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ["DB_HOST"],
    database_name=os.environ["DB_NAME"],
)

chat_manager = ChatServiceManager()
gpt_service = GptServiceManager(logger)

def is_blank_or_none(value: str):
    if value is None or value == "'":
        return True
    
    return False


@app.post("/reserve")
async def reserve(data: Reservation):
    meeting_info: dict = {
        "name": data.name if is_blank_or_none(data.name) else "no_name",
        "start_time": data.start_time if is_blank_or_none(data.start_time) else "no_start_time",
        "end_time": data.end_time if is_blank_or_none(data.end_time) else "no_end_time",
        "room": data.room if is_blank_or_none(data.room) else "no_room",
        "subject": data.subject if is_blank_or_none(data.subject) else "no_subject",
        "topic": data.topic if is_blank_or_none(data.topic) else "no_topic",
    }
    db_manager.insert_meeting_table(meeting_info)    

    for attendee in data.attendees:
        db_manager.insert_attendee_info_table(
            {
                "meeting_name": f"{meeting_info['name']}_{meeting_info['time']}",
                "name": attendee.name,
                "group": attendee.group,
                "position": attendee.position,
                "email_address": attendee.email_address,
                "role": attendee.role,
                "email_delivery_status": attendee.email_delivery_status
            }
        )

@app.get("/meeting_detail")
async def get_meeting_detail():
    meetings: List[dict] = db_manager.select_all_meeting_table()
    meeting: dict = meetings.pop()

    attendees: List[dict] = db_manager.select_all_attendee_table()

    return json.dumps({"meeting": meeting, "attendees": attendees})


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):

    await chat_manager.connect(websocket, client_id)
    logger.info(f"{chat_manager.active_connections}")

    try:
        while True:            
            data = await websocket.receive_text()
                        
            await chat_manager.broadcast(data)

    except WebSocketDisconnect:
        chat_manager.disconnect(websocket, client_id)
        # await chat_manager.broadcast(f"Client #{client_id} left the chat")
        logger.info(f"Client #{client_id} left the chat")
