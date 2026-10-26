from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
VAD_MODEL_PATH = Path(os.getenv("VAD_MODEL_PATH", str(BASE_DIR / "models" / "silero_vad.onnx")))
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2:3b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:5432/voice_rag")
PIPER_EXE = os.getenv("PIPER_EXE", "piper")
PIPER_MODEL = os.getenv("PIPER_MODEL", "models/pt_BR-faber-medium.onnx")
SAMPLE_RATE = 16_000
VAD_THRESHOLD = float(os.getenv("VAD_THRESHOLD", "0.65"))
VAD_MIN_RMS = float(os.getenv("VAD_MIN_RMS", "0.006"))
VAD_START_FRAMES = int(os.getenv("VAD_START_FRAMES", "3"))
VAD_SILENCE_MS = int(os.getenv("VAD_SILENCE_MS", "700"))
VAD_BARGE_THRESHOLD = float(os.getenv("VAD_BARGE_THRESHOLD", "0.70"))
VAD_BARGE_MIN_RMS = float(os.getenv("VAD_BARGE_MIN_RMS", "0.008"))
VAD_BARGE_START_FRAMES = int(os.getenv("VAD_BARGE_START_FRAMES", "2"))
RAG_MAX_DISTANCE = float(os.getenv("RAG_MAX_DISTANCE", "0.45"))
