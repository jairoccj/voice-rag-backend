import asyncio
import re
import threading
from app.core.connection_manager import ConversationState, GatewayAgent


async def run_turn(gateway: GatewayAgent, pcm: bytes, stt, brain, tts, cancel: threading.Event):
    try:
        await gateway.state_changed(ConversationState.TRANSCRIBING)
        transcript = await asyncio.to_thread(stt.transcribe, pcm)
        if cancel.is_set():
            return
        if not transcript:
            await gateway.state_changed(ConversationState.LISTENING)
            return
        await gateway.event("transcript", text=transcript)
        await gateway.state_changed(ConversationState.THINKING)
        sentence = ""
        async for token in brain.stream_answer(transcript, cancel):
            if cancel.is_set():
                return
            sentence += token
            if re.search(r"[.!?;:]\s*$", sentence) or len(sentence) >= 180:
                await gateway.state_changed(ConversationState.SPEAKING)
                await gateway.event("text", text=sentence)
                async for chunk in tts.synthesize(sentence, cancel):
                    await gateway.send_audio(chunk)
                    if cancel.is_set():
                        return
                sentence = ""
        if sentence.strip() and not cancel.is_set():
            await gateway.state_changed(ConversationState.SPEAKING)
            await gateway.event("text", text=sentence)
            async for chunk in tts.synthesize(sentence, cancel):
                await gateway.send_audio(chunk)
        if not cancel.is_set():
            if gateway.audio_sent:
                while not cancel.is_set() and not gateway.playback_finished.is_set():
                    try:
                        await asyncio.wait_for(gateway.playback_finished.wait(), timeout=0.05)
                    except TimeoutError:
                        continue
            await gateway.state_changed(ConversationState.LISTENING)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        await gateway.event("error", message=f"Falha no pipeline local: {exc}")
        if not cancel.is_set():
            await gateway.state_changed(ConversationState.LISTENING)
