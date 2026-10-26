"""Cancelable offline Piper subprocess, returning 16 kHz mono PCM chunks."""
import asyncio
import subprocess
import tempfile
import wave
from pathlib import Path


class TTSAgent:
    def __init__(self, executable: str = "piper", model: str = "models/pt_BR-faber-medium.onnx"):
        self.executable, self.model = executable, model

    async def synthesize(self, text: str, cancel):
        if cancel.is_set() or not text.strip():
            return
        process = None
        try:
            with tempfile.TemporaryDirectory(prefix="voice-rag-") as temp_dir:
                wav_path = Path(temp_dir) / "speech.wav"
                
                process = subprocess.Popen(
                    [self.executable, "--model", self.model, "--output_file", str(wav_path)],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    encoding="utf-8"
                )
                
                process.stdin.write(text + "\n")
                process.stdin.close()
                
                while process.poll() is None and not cancel.is_set():
                    await asyncio.sleep(0.02)
                if cancel.is_set():
                    process.terminate()
                    try:
                        process.wait(timeout=0.5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    return
                if process.returncode:
                    raise RuntimeError("Piper synthesis failed; check PIPER_EXE and PIPER_MODEL")
                with wave.open(str(wav_path), "rb") as wav:
                    rate = wav.getframerate()
                    raw = wav.readframes(wav.getnframes())
                    import numpy as np
                    pcm = np.frombuffer(raw, dtype="<i2")
                    if wav.getnchannels() > 1:
                        pcm = pcm.reshape(-1, wav.getnchannels()).mean(axis=1).astype("<i2")
                    if rate != 16000:
                        old_t = np.arange(len(pcm)) / rate
                        new_t = np.arange(round(len(pcm) * 16000 / rate)) / 16000
                        pcm = np.interp(new_t, old_t, pcm).astype("<i2")
                for offset in range(0, len(pcm), 3200):
                    if cancel.is_set():
                        return
                    yield pcm[offset:offset + 3200].tobytes()
                    await asyncio.sleep(0)
        finally:
            if process is not None and process.poll() is None:
                process.kill()
                process.wait()