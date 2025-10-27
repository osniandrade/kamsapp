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

    # Retorna apenas a transcrição, SEM gerar relatório individual
    return {"transcript": transcript, "filename": audio.filename}


@app.post("/generate_report")
async def generate_report(
    transcripts: str = Form(...),
    report_template: str = Form(...)
):
    """
    Gera um único relatório combinando todas as transcrições
    """
    import json
    
    # Parse do JSON com as transcrições
    try:
        transcripts_list = json.loads(transcripts)
    except json.JSONDecodeError as e:
        return {"error": f"Erro ao processar transcrições: {str(e)}"}
    
    # Combina todas as transcrições
    combined_transcript = "\n\n".join([
        f"### Arquivo: {t['filename']}\n{t['transcript']}" 
        for t in transcripts_list
    ])
    
    # gera o relatório com todas as transcrições combinadas
    prompt = f"""
    Você recebeu transcrições de múltiplos áudios sobre atividades de trabalho.
    
    TRANSCRIÇÕES:
    {combined_transcript}

    FORMATO DESEJADO DO RELATÓRIO:
    {report_template}

    Gere um relatório consolidado seguindo exatamente o formato acima, 
    organizando todas as informações das transcrições de forma estruturada.
    Remova do relatório final qualquer informação que não esteja nas transcrições.
    Use markdown para formatação.
    Responda em português brasileiro.
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
        print(f"Gerando relatório consolidado com {len(transcripts_list)} transcrições...")
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=90)
        print(f"Status OpenRouter: {response.status_code}")
        response.raise_for_status()
        data = response.json()

        report = data["choices"][0]["message"]["content"]
        return {"report": report}

    except Exception as e:
        print(f"Erro ao gerar relatório: {str(e)}")
        return {"error": str(e)}
