"""Local faster-whisper transcription; inference runs off the event loop."""
import io
import wave
import av
from faster_whisper import WhisperModel


# faster-whisper passes metadata_errors to av.open, while some newer PyAV
# wheels removed that keyword. It only controls metadata parse error handling;
# dropping it preserves audio decoding and avoids pinning a native AV wheel.
_av_open = av.open


def _compatible_av_open(*args, **kwargs):
    kwargs.pop("metadata_errors", None)
    return _av_open(*args, **kwargs)


av.open = _compatible_av_open


class STTAgent:
    def __init__(self, model_name: str = "base"):
        self.model = WhisperModel(model_name, device="cpu", compute_type="int8")

    def transcribe(self, pcm: bytes, sample_rate: int = 16000, initial_prompt: str | None = None) -> str:
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(pcm)
        buffer.seek(0)
        segments, _ = self.model.transcribe(buffer, language="pt", initial_prompt=initial_prompt or "Conversa em português brasileiro sobre documentos, sistemas, tecnologia, áudio e perguntas do usuário.", beam_size=1, vad_filter=False)
        return " ".join(segment.text.strip() for segment in segments).strip()
