from fastapi import BackgroundTasks, Depends, FastAPI, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from typing import Optional
from functools import lru_cache
import logging
import config
from pydantic import BaseModel
import requests


logging.basicConfig(filename="logging.conf")


@lru_cache()
def get_settings():
    return config.Settings()


app = FastAPI()
templates = Jinja2Templates(directory="replymessage")


class SlackEvent(BaseModel):
    type: str
    channel: str
    user: str
    ts: str
    thread_ts: Optional[str]
    channel_type: str
    text: str


class SlackRequest(BaseModel):
    token: str
    challenge: Optional[str]
    type: str
    event: SlackEvent


def is_sender_a_bot(event: SlackEvent) -> bool:
    params_payload = {
        "user": event.user,
    }
    headers_payload = {
        "Authorization": f"Bearer {get_settings().slack_oauth_token}"
    }
    response = requests.get("https://slack.com/api/users.info",
                            params=params_payload, headers=headers_payload)
    if response.ok:
        return response.json().get("user", {}).get("is_bot", True)
    return True


async def respond_in_thread(event: SlackEvent):
    is_response_required = True
    if is_sender_a_bot(event):
        is_response_required = False
    if event.thread_ts:
        is_response_required = False
    if not is_response_required:
        return

    message = None
    with open(get_settings().message_file_name, 'r') as file:
        message = file.read()

    payload = {
        "token": get_settings().slack_oauth_token,
        "text": message,
        "channel": event.channel,
        "thread_ts": event.ts
    }

    r = requests.post('https://slack.com/api/chat.postMessage', data=payload)

    log_message = f"Status: {r.status_code}\nBody: {r.json()}"
    logging.info(log_message)


@app.post("/editMessage")
async def handle_edit_message(message: str = Form(...), settings: config.Settings = Depends(get_settings)):
    with open(settings.message_file_name, 'w+') as file:
        file.write(message)
    return {"message": message}


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    logging.info(str(request))
    return replyMessage.TemplateResponse("index.html", {"request": request})


@app.post("/")
async def handle_slack_event(request: SlackRequest, background_tasks: BackgroundTasks):
    logging.info(request)
    print(request)
    type = request.type
    if request.type == "url_verification":
        return get_challenge_response(request)
    elif request.type == "event_callback":
        background_tasks.add_task(respond_in_thread, request.event)


async def get_challenge_response(request: SlackRequest):
    background_tasks.add_task(get_identity)
    return {"challenge": request.challenge}
