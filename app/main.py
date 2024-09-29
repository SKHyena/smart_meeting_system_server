import json
import os
import logging
import time
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status, HTTPException

from .provider.database_manager import DatabaseManager
from .service.chat_service import ChatServiceManager
from .service.llm.gpt_service import GptServiceManager
from .model.dialogue import Dialogue
from .model.utterance import Utterance
from .util.time_util import TimeUtil


app = FastAPI()
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)

db_manager = DatabaseManager(
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ["DB_HOST"],
    database_name=os.environ["DB_NAME"],
)
# db_manager.drop_complaint_table()
# db_manager.drop_total_complaint_table()
db_manager.create_complaint_table()
db_manager.create_total_complaint_table()

chat_manager = ChatServiceManager()
gpt_service = GptServiceManager(logger)


@app.get("/counsel_list")
async def get_counsel_list():
    data = db_manager.select_all_total_complaint_table()
    if len(data) == 0:
        return []
    
    counsel_list = []
    for record in data:
        dialogue = json.loads(record["dialogue"])
        
        if len(dialogue) == 0:
            timestamp = TimeUtil.convert_unixtime_to_timestamp(int(time.time()))
        else:
            timestamp = TimeUtil.convert_unixtime_to_timestamp(dialogue["dialogue"][0]["timestamp"])
            
        locales = {x["locale"] for x in dialogue["dialogue"] if x["locale"] != "ko"}
        locale = locales.pop() if len(locales) > 0 else "ko"

        counsel_list.append({
            "id": record["id"],
            "timestamp": timestamp,
            "locale": locale,
            "category": record["category"],
            "summary": record["summary"]
        })

    return counsel_list


@app.get("/counsel_list/{counsel_id}")
async def get_counsel_detail(counsel_id: int):
    record = db_manager.select_total_complaint_table_with_id(counsel_id)

    if len(record) == 0:
        return {}
    
    return record[0]["dialogue"]


def filter_dialogue(dialogue: List[Utterance]) -> List[dict]:
    filtered_dialogue = []

    for utterance in dialogue:
        if utterance.speaker == "complainant":
            filtered_dialogue.append(
                {
                    "timestamp": utterance.timestamp,
                    "speaker": utterance.speaker,
                    "text": utterance.translated_text
                }
            )
        else:
            filtered_dialogue.append(
                {
                    "timestamp": utterance.timestamp,
                    "speaker": utterance.speaker,
                    "text": utterance.origin_text
                }
            )
    return filtered_dialogue


@app.post("/finish_counsel")
async def wrapup_counsel(data: Dialogue):
    try:
        filtered_dialogue = filter_dialogue(data.dialogue)
        logger.info(f"dialogue: {filtered_dialogue}")

        db_manager.insert_total_complaint_table(
            {
                "category": gpt_service.categorize(filtered_dialogue), 
                "summary": gpt_service.summarize(filtered_dialogue).strip(),
                "dialogue": data.model_dump_json(),
            }
        )
    except:
        return HTTPException(status_code=status.WS_1011_INTERNAL_ERROR)

    return status.HTTP_200_OK
    

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):

    await chat_manager.connect(websocket, client_id)
    logger.info(f"{chat_manager.active_connections}")

    try:
        while True:            
            data = await websocket.receive_text()
            dict_data = json.loads(data)

            if "init" in dict_data:
                chat_manager.client_locale[client_id] = dict_data["locale"]                
                if client_id == 1 and 0 in chat_manager.active_connections:                
                    await chat_manager.send_personal_message("Complainant has entered", 1)
                    await chat_manager.send_personal_message(
                        json.dumps({"locale": chat_manager.client_locale[0]}), 1
                    )
                
                if client_id == 0 and 1 in chat_manager.active_connections:
                    await chat_manager.send_personal_message("Complainant has entered", 1)
                    await chat_manager.send_personal_message(
                        json.dumps({"locale": chat_manager.client_locale[0]}), 1
                    )

            else:
                await chat_manager.broadcast(data)
                db_manager.insert_complaint_table(dict_data)

    except WebSocketDisconnect:
        chat_manager.disconnect(websocket, client_id)
        # await chat_manager.broadcast(f"Client #{client_id} left the chat")
        logger.info(f"Client #{client_id} left the chat")
