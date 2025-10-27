from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import requests
import subprocess
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

    # executa whisper.cpp via CLI
    result = subprocess.run(
        [
            "docker", "exec", "whisper-service",
            "./main", "-m", "models/ggml-base.en.bin", "-f", f"/data/{audio.filename}", "-otxt"
        ],
        capture_output=True, text=True
    )

    transcript_file = f"{file_path}.txt"
    if not os.path.exists(transcript_file):
        return {"error": "Erro ao transcrever áudio."}

    with open(transcript_file, "r") as f:
        transcript = f.read()

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
