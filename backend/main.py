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
    try:
        with open(file_path, "wb") as f:
            f.write(await audio.read())
    except Exception as e:
        return {"error": f"Erro ao salvar arquivo: {str(e)}"}

    # chama a API do faster-whisper (openai-whisper-asr-webservice)
    whisper_url = "http://faster-whisper:9000/asr"
    
    try:
        print(f"Processando arquivo: {audio.filename}, tamanho: {os.path.getsize(file_path)} bytes")
        
        with open(file_path, "rb") as audio_file:
            files = {"audio_file": audio_file}
            data = {
                "task": "transcribe",
                "language": "pt",
                "output": "json"
            }
            
            print(f"Enviando para {whisper_url}...")
            whisper_response = requests.post(whisper_url, files=files, data=data, timeout=300)
            print(f"Status code: {whisper_response.status_code}")
            print(f"Response content: {whisper_response.text[:500]}")
            whisper_response.raise_for_status()
            
            # Try to parse JSON response
            try:
                transcript_data = whisper_response.json()
                print(f"Resposta JSON recebida: {transcript_data}")
                transcript = transcript_data.get("text", "")
            except ValueError as json_err:
                # If not JSON, the response text might BE the transcript
                print(f"Não é JSON, usando texto direto: {whisper_response.text[:200]}")
                transcript = whisper_response.text.strip()
            
            if not transcript:
                return {"error": "Transcrição vazia retornada pelo Whisper."}
                
    except requests.exceptions.ConnectionError:
        return {"error": "Não foi possível conectar ao serviço de transcrição. Verifique se o faster-whisper está rodando."}
    except requests.exceptions.Timeout:
        return {"error": "Timeout ao transcrever áudio. O arquivo pode ser muito longo."}
    except Exception as e:
        return {"error": f"Erro ao transcrever áudio: {str(e)}"}
    finally:
        # Remove o arquivo após processar
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass

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
