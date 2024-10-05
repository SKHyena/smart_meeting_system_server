import json
import os
import logging
import io
import urllib
import time
from typing import List, Any
from pathlib import Path
import urllib.parse


import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Form, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse

from .provider.database_manager import DatabaseManager
from .service.chat_service import ChatServiceManager
from .service.llm.gpt_service import GptServiceManager
from .model.file_info import FileInfo
from .model.attendee import Attendance
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
# db_manager.drop_meeting_table()
# db_manager.drop_attendee_table()
db_manager.create_meeting_table()
db_manager.create_attendee_table()

s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.environ["OBJECT_STORAGE_ACCESS_KEY"],
    aws_secret_access_key=os.environ["OBJECT_STORAGE_SECRET_KEY"],
    region_name='kr-standard',
    endpoint_url='https://kr.object.ncloudstorage.com'
)

chat_manager = ChatServiceManager()
gpt_service = GptServiceManager(logger)

save_dir = Path("/uploaded_files")
save_dir.mkdir(parents=True, exist_ok=True)


def is_blank_or_none(value: str):
    if value is None or value == "'":
        return True
    
    return False


@app.post("/reserve")
async def reserve(
    reserve_data: str = Form(...),
    attendees_data: str = Form(...),
    files: List[UploadFile] = File(...),
):    
    files_info = []

    for file in files:                
        try:
            s3_client.put_object(
                Bucket="ggd-bucket01",
                Key=file.filename,
                Body=file.file,
            )
            files_info.append({"file": file.filename})
        except NoCredentialsError:
            raise HTTPException(status_code=401, detail="Naver Cloud credentials not available")
        except PartialCredentialsError:
            raise HTTPException(status_code=401, detail="Incomplete Naver Cloud credentials")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")
        
    meeting_info: dict[str, Any] = json.loads(reserve_data)
    meeting_info["files"] = json.dumps(files_info, ensure_ascii=False)
    db_manager.insert_meeting_table(meeting_info)

    attendees: List[dict[str, Any]] = json.loads(attendees_data)

    for attendee in attendees:    
        attendee["meeting_name"] = f"{meeting_info['name']}_{meeting_info['start_time']}"
        db_manager.insert_attendee_info_table(attendee)


@app.get("/meeting_detail")
async def get_meeting_detail():
    meetings: tuple[dict] = db_manager.select_all_meeting_table()
    meeting: dict = meetings[-1] if len(meetings) >= 1 else {}

    attendees: tuple[dict] = db_manager.select_all_attendee_table()

    return {"meeting": meeting, "attendees": list(attendees)}


@app.post("/download_file")
async def download_file(file_info: FileInfo):    
    try:                
        logger.info(f"file name : {file_info.file_name}")        
        s3_object = s3_client.get_object(Bucket="ggd-bucket01", Key=file_info.file_name)
        return StreamingResponse(
            io.BytesIO(s3_object['Body'].read()), 
            media_type="application/octet-stream", 
            headers={"Content-Disposition": f"attachment; filename*=UTF-8\'\'{urllib.parse.quote(file_info.file_name)}"},
        )
    except NoCredentialsError:
        raise HTTPException(status_code=401, detail="AWS Credentials not available")
    except PartialCredentialsError:
        raise HTTPException(status_code=401, detail="Incomplete AWS credentials")
    except s3_client.exceptions.NoSuchKey:
        raise HTTPException(status_code=404, detail="File not found in S3 bucket")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File download failed: {str(e)}")
    

@app.post("/attend")
async def attend(attendance: Attendance):
    attendance_info: dict[str, Any] = attendance.model_dump()
    attendance_info["attendance_status"] = True
    attendance_info["initial_attendance_time"] = TimeUtil.convert_unixtime_to_timestamp(time.time())

    db_manager.update_attendee_attendance_info_table(attendance_info)    


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
