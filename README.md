# Audio Transcriber Web App

Audio transcription and report generation application using Faster Whisper and OpenRouter AI.

## Issues Fixed

1. **Backend transcription logic**: Changed from incorrect `docker exec whisper-service` with whisper.cpp to proper API calls to the faster-whisper service at `http://faster-whisper:10300/api/transcribe`

2. **Missing directories**: Created required `uploads/`, `audio/`, and `output/` directories referenced in docker-compose.yaml

3. **Import cleanup**: Removed unnecessary `subprocess` import from backend

## How to Run

1. Make sure Docker is installed and running

2. Start the application:
```bash
docker compose up -d --build
```

3. Access the frontend at: http://localhost:8080

4. The backend API is available at: http://localhost:8000

## Services

- **Frontend**: Nginx serving static HTML/JS at port 8080
- **Backend**: FastAPI service at port 8000
- **Faster-Whisper**: Whisper transcription service at port 10300

## Usage

1. Open http://localhost:8080 in your browser
2. Drag and drop an audio file or click to select one
3. Enter your desired report template format
4. Click "Enviar e Gerar Relatório"
5. View the transcription and AI-generated report

## Environment Variables

The backend requires these variables in `backend/.env`:
- `OPENROUTER_API_KEY`: Your OpenRouter API key
- `OPENROUTER_MODEL`: AI model to use (default: openai/gpt-4o)
