from fastapi import FastAPI, Query, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import random
import time
import re
from helpers import get_audio_file
from helpers import parse_file
import shutil
from helpers import parse_url
import uuid



app = FastAPI()

# Путь к общей директории
SHARED_DIR = "/app/shared"

# Mount static files (including favicon)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/shared", StaticFiles(directory=SHARED_DIR), name="shared")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return HTMLResponse(content="<h1>T-ОбъясняшкI</h1>")

@app.post("/chat")
async def chat(message: str = Query(..., min_length=1)):
    try:
        # Проверяем, является ли сообщение ссылкой
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        is_url = bool(url_pattern.match(message))

        text = ""
        if is_url:
            text = parse_url(message) 
        else:
            text = message
        
        response = get_audio_file(text)
        if response["responses"] == "error":
            raise HTTPException(status_code=500, detail=f"Ошибка при обработке сообщения: {response['responses']}")
        
        return JSONResponse(content=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обработке сообщения: {str(e)}")

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Сохраняем файл в общую директорию
        file_path = os.path.join(SHARED_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        

        message = f"Файл {file.filename} загружен"
        
        parsed_text = parse_file(file_path)
        response = get_audio_file(parsed_text)        
        time.sleep(3)
        
        return JSONResponse(content=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)