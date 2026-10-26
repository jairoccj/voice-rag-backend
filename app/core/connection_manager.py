from enum import StrEnum
from fastapi import WebSocket


class ConversationState(StrEnum):
    IDLE = "idle"
    LISTENING = "listening"
    TRANSCRIBING = "transcribing"
    THINKING = "thinking"
    SPEAKING = "speaking"
    INTERRUPTED = "interrupted"


class GatewayAgent:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.state = ConversationState.IDLE
        self.send_lock = __import__("asyncio").Lock()
        self.playback_finished = __import__("asyncio").Event()
        self.audio_sent = False

    def begin_turn(self):
        self.audio_sent = False
        self.playback_finished.clear()

    def mark_playback_finished(self):
        self.playback_finished.set()

    async def event(self, kind: str, **payload):
        async with self.send_lock:
            await self.websocket.send_json({"type": kind, **payload})

    async def state_changed(self, state: ConversationState):
        self.state = state
        await self.event("state", state=state.value)

    async def send_audio(self, pcm: bytes):
        self.audio_sent = True
        # A new chunk may arrive after a previous sentence drained from the
        # browser queue. The final acknowledgement must correspond to the last chunk.
        self.playback_finished.clear()
        async with self.send_lock:
            await self.websocket.send_bytes(pcm)
