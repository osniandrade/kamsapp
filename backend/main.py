from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import requests
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

@app.post("/process_audio")
async def process_audio(
    audio: UploadFile = File(...),
    report_template: str = Form(...)
):
    file_path = os.path.join(UPLOAD_DIR, audio.filename)

    # salva o arquivo de áudio
    with open(file_path, "wb") as f:
        f.write(await audio.read())

    # chama a API do faster-whisper
    whisper_url = "http://faster-whisper:10300/api/transcribe"
    
    try:
        with open(file_path, "rb") as audio_file:
            files = {"audio_file": (audio.filename, audio_file, audio.content_type)}
            data = {"language": "pt"}
            
            whisper_response = requests.post(whisper_url, files=files, data=data, timeout=120)
            whisper_response.raise_for_status()
            
            transcript_data = whisper_response.json()
            transcript = transcript_data.get("text", "")
            
            if not transcript:
                return {"error": "Transcrição vazia retornada pelo Whisper."}
    
    except Exception as e:
        return {"error": f"Erro ao transcrever áudio: {str(e)}"}

    # gera o relatório com ChatGPT / DeepSeek
    prompt = f"""
    Texto original: {transcript}

    Formato desejado do relatório:
    {report_template}

    Gere um relatório seguindo exatamente o formato acima.
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()

        report = data["choices"][0]["message"]["content"]
        return {"transcript": transcript, "report": report}

    except Exception as e:
        return {"error": str(e), "transcript": transcript}
