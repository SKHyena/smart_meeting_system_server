import json
import os
import logging
import io
import urllib
import time
import asyncio
from typing import List, Any, Optional, Union

import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Form, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from google.cloud import speech

from .provider.database_manager import DatabaseManager
from .service.chat_service import ChatServiceManager
from .service.llm.gpt_service import GptServiceManager
from .service.mail_service import MailServiceManager
from .service.transcribe_service import TranscriptionService
from .model.file_info import FileInfo
from .model.attendee import Attendance
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
mail_service = MailServiceManager(
    os.environ["MAIL_ACCOUNT"],
    os.environ["MAIL_APP_NUMBER"].replace("_", " ")
)
# transcription_service = TranscriptionService(logger=logger)

# Google Speech Client 설정
client = speech.SpeechClient()

# Google Speech API의 인식 설정
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,  # 오디오 인코딩 방식
    sample_rate_hertz=48000,  # 샘플 레이트 (클라이언트의 마이크에 맞게 조정 가능)
    language_code="ko-KR"  # 인식할 언어 코드
)


def is_blank_or_none(value: str):
    if value is None or value == "'":
        return True
    
    return False


@app.post("/reserve", status_code=201)
async def reserve(
    reserve_data: str = Form(...),
    attendees_data: str = Form(...),
    files: List[Union[UploadFile, None]] = File(None)
):
    db_manager.delete_all_meeting_table()
    db_manager.delete_all_attendee_table()

    files_info = []
    if files is not None:        
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
    meeting_info["pt_contents"] = "Presentation contents should be updated"
    meeting_info["status"] = "회의 시작 전"
    db_manager.insert_meeting_table(meeting_info)

    attendees: List[dict[str, Any]] = json.loads(attendees_data)
    for attendee in attendees:    
        attendee["meeting_name"] = f"{meeting_info['name']}_{meeting_info['start_time']}"
        db_manager.insert_attendee_info_table(attendee)


@app.get("/update_meeting/{status}", status_code=200)
async def update_meeting(status: str):
    meeting_status: dict[str, int] = {
        "회의 시작 전": 1,
        "PT발표": 2,
        "Q&A": 3,
        "회의 종료상태": 4,
        "정회": 98, 
        "재개": 99,
    }

    if status not in meeting_status:
        return HTTPException(500, "meeting status is not correct.")
    logger.info(f"Update meeting status : {status}")
    
    if status not in ["정회", "재개"]:
        db_manager.update_meeting_status_table(status)

    await chat_manager.broadcast(json.dumps(
        {"type": "meeting_status", "status": meeting_status[status]}
    ))


@app.get("/meeting_detail", status_code=200)
async def get_meeting_detail():
    meetings: tuple[dict] = db_manager.select_all_meeting_table()
    meeting: dict = meetings[-1] if len(meetings) >= 1 else {}

    attendees: tuple[dict] = db_manager.select_all_attendee_table()

    return {"meeting": meeting, "attendees": list(attendees)}


@app.post("/download_file", status_code=201)
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
    

@app.post("/attend", status_code=201)
async def attend(attendance: Attendance):
    attendance_info: dict[str, Any] = attendance.model_dump()
    attendance_info["attendance_status"] = True
    attendance_info["initial_attendance_time"] = TimeUtil.convert_unixtime_to_timestamp(int(time.time()))

    db_manager.update_attendee_attendance_info_table(attendance_info)


@app.get("/mail_send/{client_id}", status_code=200)
async def send_mail(client_id: int):
    attendees = db_manager.select_attendee_table_with_id(client_id)
    summary: str = db_manager.select_all_meeting_table()[0]["summary"]

    if summary is None or summary == "":
        return HTTPException(500, "Summary has not been updated.")    

    try:
        for attendee in attendees:
            address: str = attendee["email_address"]        
            content = mail_service.build_email(address, summary)
            mail_service.send_email(content)
    except:
        return HTTPException(500, "Sending e-mail failed")


@app.get("/mail_send", status_code=201)
async def send_mail():
    attendees = db_manager.select_all_attendee_table()
    summary: str = db_manager.select_all_meeting_table()[0]["summary"]

    if summary is None or summary == "":
        return HTTPException(500, "Summary has not been updated.")    
    
    try:
        for attendee in attendees:
            if attendee["email_delivery_status"] == 0:
                continue

            address: str = attendee["email_address"]        
            content = mail_service.build_email(address, summary)
            mail_service.send_email(content)
    except:
        return HTTPException(500, "Sending e-mail failed")


@app.get("/summarize", status_code=201)
async def summarize():
    attendees = db_manager.select_all_attendee_table()
    attendee_id_name_map = {
        attendee["id"]: attendee["name"] for attendee in attendees
    }

    utterances: List[Utterance] = chat_manager.qa_list.copy()
    for utterance in utterances:
        utterance.speaker = attendee_id_name_map[utterance.speaker]

    summary: str = gpt_service.summarize(utterances)
    logger.info(f"Summary : \n {summary}")
    db_manager.update_meeting_summary_table(summary)

    return {"summary": summary}


# @app.websocket("/ws/transcribe/{client_id}")
# async def websocket_endpoint(websocket: WebSocket, client_id: int):
#     await websocket.accept()
#     try:
#         while True:
#             bytes_arr = await websocket.receive_bytes()            
#             text = transcription_service.transcribe(bytes_arr)
#             logger.info(f"transcribed text : {text}")
#             await websocket.send_text(text)
#             # chat_manager.broadcast(
#             #     json.dumps({
#             #         "type": "q&a",
#             #         "id": client_id,
#             #         "is_done": False,
#             #         "timestamp": int(time.time())
#             #     })
#             # )

#     except WebSocketDisconnect:        
#         logger.info(f"Client #{client_id} left the transcription websocket channel")


@app.websocket("/ws/transcribe/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await websocket.accept()

    # Google Speech API에 전송할 스트림 생성
    def generate_audio_requests():
        while True:
            # 계속해서 데이터를 WebSocket으로부터 받음
            audio_chunk = yield
            if audio_chunk:
                yield speech.StreamingRecognizeRequest(audio_content=audio_chunk)

    # 스트림 요청 생성기
    audio_requests = generate_audio_requests()
    next(audio_requests)  # 첫 번째 호출로 제너레이터 준비

    try:
        # Google Speech-to-Text API의 스트리밍 인식 호출
        streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=True)
        responses = client.streaming_recognize(streaming_config, audio_requests)

        async def receive_audio():
            """클라이언트로부터 오디오 데이터를 WebSocket으로 받음"""
            while True:
                try:
                    data = await websocket.receive_bytes()
                    audio_requests.send(data)
                except WebSocketDisconnect:
                    break

        async def process_speech():
            """Google Speech API에서 받은 텍스트 결과를 처리"""
            for response in responses:
                for result in response.results:
                    logger.info(f"Recognized text: {result.alternatives[0].transcript}")
                    await websocket.send_text(f"Recognized: {result.alternatives[0].transcript}")

        # 오디오 수신 및 텍스트 변환 동시 처리
        await asyncio.gather(receive_audio(), process_speech())

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")    


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await chat_manager.connect(websocket, client_id)

    # mic_status: dict[int, str] = {}
    # for id in chat_manager.mic_status:
    #     mic_status[id] = "on" if chat_manager.mic_status[id] else "off"
    # await chat_manager.send_personal_message(json.dumps(mic_status), client_id)    
    logger.info(f"{chat_manager.active_connections}")

    try:
        while True:
            data: str = await websocket.receive_text()
            json_data: dict = json.loads(data)

            if json_data["type"] == "mic":
                logger.info(f"{client_id} client has changed mic status : {json_data['status']}")

            if json_data["type"] == "q&a" and json_data["id_done"]:                
                logger.info(f"Q&A message: {json_data['message']}")
                chat_manager.qa_list.append(
                    Utterance(
                        timestamp=TimeUtil.convert_unixtime_to_timestamp(json_data["timestamp"]),
                        speaker=json_data["id"],
                        text=json_data["message"]
                    )
                )

            await chat_manager.broadcast(data)

    except WebSocketDisconnect:
        chat_manager.disconnect(websocket, client_id)
        # await chat_manager.broadcast(f"Client #{client_id} left the chat")
        logger.info(f"Client #{client_id} left the chat")
