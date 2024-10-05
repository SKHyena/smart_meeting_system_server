import json
import os
import logging
import time
from typing import List, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Form, UploadFile, File

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
# db_manager.drop_meeting_table()
# db_manager.drop_attendee_table()
db_manager.create_meeting_table()
db_manager.create_attendee_table()

chat_manager = ChatServiceManager()
gpt_service = GptServiceManager(logger)

def is_blank_or_none(value: str):
    if value is None or value == "'":
        return True
    
    return False


@app.post("/reserve")
async def reserve(data: Reservation):
    meeting_info: dict[str, Any] = data.model_dump()
    db_manager.insert_meeting_table(meeting_info)

    for attendee in data.attendees:
        attendee_dict = attendee.model_dump()
        attendee_dict["meeting_name"] = f"{meeting_info['name']}_{meeting_info['time']}"

        db_manager.insert_attendee_info_table(attendee_dict)

@app.post("/reserve2")
async def reserve(
    reserve_data: str = Form(...),
    attendees_data: str = Form(...),
    files: List[UploadFile] = File(...),
):
    meeting_info: dict[str, Any] = json.loads(reserve_data)
    db_manager.insert_meeting_table(meeting_info)

    attendees: List[dict[str, Any]] = json.loads(attendees_data)

    for attendee in attendees:    
        attendee["meeting_name"] = f"{meeting_info['name']}_{meeting_info['time']}"
        db_manager.insert_attendee_info_table(attendee)

    # File 처리합시다.
    for file in files:
        content = await file.read()



@app.get("/meeting_detail")
async def get_meeting_detail():
    meetings: List[dict] = db_manager.select_all_meeting_table()
    meeting: dict = meetings.pop()

    attendees: List[dict] = db_manager.select_all_attendee_table()

    return {"meeting": meeting, "attendees": attendees}


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
