import os
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from text_to_ssml.utils import get_text_from_string, ERROR_MESSAGE
from text_to_speech.voicekit.python.snippets.generate import generate_audio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

SHARED_DIR = "/app/shared"

class GenerateRequest(BaseModel):
    querry: str

class GenerateResponse(BaseModel):
    generated_text: str
    audio_filename: str

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    try:
        logger.info(f"Received request with query: {request.querry[:50]}...")
        
        generated_text, dialog_in_one_string = await get_text_from_string(request.querry)
        logger.info(f"Generated text: {generated_text[:50]}...")
        
        audio_filename = f"{uuid.uuid4()}.wav"
        audio_path = os.path.join(SHARED_DIR, audio_filename)
        logger.info(f"Generating audio to path: {audio_path}")
        
        generate_audio(generated_text, audio_path)
        
        logger.info("Audio generated successfully")
        
        return GenerateResponse(
            generated_text=dialog_in_one_string,
            audio_filename=audio_filename
        )  
    except Exception as e:
        logger.error(f"Error in generate endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
