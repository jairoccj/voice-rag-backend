"""FastAPI WebSocket gateway for fully local real-time voice conversation."""
import asyncio
import json
import logging
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from app.config import (
    VAD_MODEL_PATH, VAD_THRESHOLD, VAD_MIN_RMS, VAD_START_FRAMES,
    VAD_SILENCE_MS, VAD_BARGE_THRESHOLD, VAD_BARGE_MIN_RMS,
    VAD_BARGE_START_FRAMES, WHISPER_MODEL, PIPER_EXE, PIPER_MODEL,
)
from app.core.connection_manager import ConversationState, GatewayAgent
from app.core.pipeline import run_turn
from app.services.vad import VADAgent
from app.services.stt import STTAgent
from app.services.rag import BrainAgent
from app.services.tts import TTSAgent


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Keep heavyweight local models loaded once per process.
    app.state.vad_path = VAD_MODEL_PATH
    app.state.stt = None
    app.state.brain = BrainAgent()
    app.state.tts = TTSAgent(PIPER_EXE, PIPER_MODEL)
    yield
    await app.state.brain.close()

app = FastAPI(title="Offline Voice RAG", lifespan=lifespan)
logger = logging.getLogger("voice")


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse("index.html")


@app.get("/app.js", include_in_schema=False)
async def frontend_script():
    return FileResponse("app.js", media_type="text/javascript")


@app.get("/health")
async def health():
    return {"status": "ok", "offline": True}


@app.websocket("/ws/voice")
async def voice_socket(websocket: WebSocket):
    await websocket.accept()
    logger.info("Voice WebSocket accepted from %s", websocket.client)
    gateway = GatewayAgent(websocket)
    vad = None
    turn_task = None
    cancel = threading.Event()
    audio_packets = 0
    try:
        # Heavy initialization is lazy so HTTP health remains available if local
        # model assets have not been installed yet; errors are reported to client.
        try:
            await gateway.event("status", message="Carregando VAD e Whisper locais…")
            vad = await asyncio.to_thread(
                VADAgent,
                app.state.vad_path,
                VAD_THRESHOLD,
                VAD_SILENCE_MS,
                VAD_MIN_RMS,
                VAD_START_FRAMES,
                VAD_BARGE_THRESHOLD,
                VAD_BARGE_MIN_RMS,
                VAD_BARGE_START_FRAMES,
            )
            if app.state.stt is None:
                app.state.stt = await asyncio.to_thread(STTAgent, WHISPER_MODEL)
        except Exception as exc:
            logger.exception("Failed loading local voice models")
            await gateway.event("error", message=f"Falha ao carregar modelos locais: {exc}")
            await websocket.close(code=1011)
            return
        await gateway.state_changed(ConversationState.LISTENING)
        while True:
            packet = await websocket.receive()
            if packet.get("type") == "websocket.disconnect":
                break
            data = packet.get("bytes")
            if data is None:
                message_text = packet.get("text")
                if message_text:
                    try:
                        message = json.loads(message_text)
                    except json.JSONDecodeError:
                        continue
                    if message.get("type") == "playback_done":
                        gateway.mark_playback_finished()
                continue
            audio_packets += 1
            if audio_packets == 1:
                logger.info("First microphone packet received (%d bytes)", len(data))
            started, completed = await asyncio.to_thread(
                vad.process,
                data,
                during_playback=gateway.state == ConversationState.SPEAKING,
            )
            if audio_packets % 10 == 0:
                await gateway.event(
                    "audio_level",
                    rms=round(vad.last_rms, 4),
                    vad=round(vad.last_probability, 4),
                    packets=audio_packets,
                )
            if started:
                logger.info("Speech start detected (VAD %.3f)", vad.last_probability)
            if completed:
                logger.info("Speech end detected (%d bytes); starting STT", len(completed))
            if started and gateway.state in {ConversationState.SPEAKING, ConversationState.THINKING, ConversationState.TRANSCRIBING}:
                cancel.set()
                if turn_task and not turn_task.done():
                    turn_task.cancel()
                    await asyncio.gather(turn_task, return_exceptions=True)
                await gateway.state_changed(ConversationState.INTERRUPTED)
                await gateway.event("interrupt")
                cancel = threading.Event()
                # VAD already buffered the beginning of the new utterance.
                await gateway.state_changed(ConversationState.LISTENING)
            if completed:
                if turn_task and not turn_task.done():
                    cancel.set()
                    turn_task.cancel()
                    await asyncio.gather(turn_task, return_exceptions=True)
                cancel = threading.Event()
                gateway.begin_turn()
                turn_task = asyncio.create_task(run_turn(gateway, completed, app.state.stt, app.state.brain, app.state.tts, cancel))
    except WebSocketDisconnect:
        pass
    finally:
        cancel.set()
        if turn_task and not turn_task.done():
            turn_task.cancel()
            await asyncio.gather(turn_task, return_exceptions=True)
