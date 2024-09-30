import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse  # Для favicon
from telethon import TelegramClient, functions, types
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
from pydantic import BaseModel

app = FastAPI()

api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')
session_file_path = 'session_name'

class PhoneNumber(BaseModel):
    phone: str

class OTPVerification(BaseModel):
    phone: str
    code: str
    phone_code_hash: str

class StoryRequest(BaseModel):
    peer: str
    file_path: str
    spoiler: bool = True
    ttl_seconds: int = 42

# Маршрут для корневой страницы
@app.get("/")
async def root():
    return {"message": "Hello, welcome to the Telegram bot API!"}

# Маршрут для favicon
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return RedirectResponse(url="/static/favicon.ico")

# Маршрут для webhook
@app.post("/api/webhook")
async def webhook():
    return {"message": "Webhook receiцукцукцукved successfully"}

# Маршрут для генерации OTP
@app.post("/generate_otp")
async def generate_otp(phone_number: PhoneNumber):
    try:
        client = TelegramClient(session_file_path, api_id, api_hash)
        await client.connect()
        result = await client.send_code_request(phone_number.phone, force_sms=True)
        phone_hash = result.phone_code_hash
        await client.disconnect()
        return {"phone_code_hash": phone_hash}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Маршрут для верификации OTP
@app.post("/verify_otp")
async def verify_otp(otp_verification: OTPVerification):
    try:
        client = TelegramClient(session_file_path, api_id, api_hash)
        await client.connect()
        await client.sign_in(
            otp_verification.phone,
            code=otp_verification.code,
            phone_code_hash=otp_verification.phone_code_hash,
        )
        user = await client.get_me()
        await client.disconnect()
        return {"message": f"Authenticated as {user.first_name}"}
    except SessionPasswordNeededError:
        raise HTTPException(status_code=401, detail="Two-step verification is enabled. Please provide the password.")
    except PhoneCodeInvalidError:
        raise HTTPException(status_code=401, detail="Invalid code provided.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Маршрут для отправки истории
@app.post("/send_story")
async def send_story(story_request: StoryRequest):
    try:
        client = TelegramClient(session_file_path, api_id, api_hash)
        await client.connect()
        if not await client.is_user_authorized():
            raise HTTPException(status_code=401, detail="Unauthorized. Please authenticate first.")

        result = await client(functions.stories.SendStoryRequest(
            peer=story_request.peer,
            media=types.InputMediaUploadedPhoto(
                file=await client.upload_file(story_request.file_path),
                spoiler=story_request.spoiler,
                ttl_seconds=story_request.ttl_seconds
            ),
            privacy_rules=[types.InputPrivacyValueAllowContacts()]
        ))
        await client.disconnect()
        return {"message": "Story sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
