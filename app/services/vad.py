"""Streaming Silero ONNX VAD for mono 16 kHz PCM16 input."""
from collections import deque
from pathlib import Path
import numpy as np
import onnxruntime as ort

FRAME_SAMPLES = 512


class VADAgent:
    def __init__(
        self,
        model_path: Path,
        threshold: float = 0.65,
        silence_ms: int = 700,
        min_rms: float = 0.006,
        start_frames: int = 3,
        barge_threshold: float = 0.82,
        barge_min_rms: float = 0.025,
        barge_start_frames: int = 5,
    ):
        if not model_path.is_file():
            raise FileNotFoundError(f"Silero VAD ONNX model not found: {model_path}")
        self.session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
        self.inputs = {item.name: item for item in self.session.get_inputs()}
        self.threshold = threshold
        self.continuation_threshold = max(0.20, threshold - 0.25)
        self.barge_threshold = max(barge_threshold, threshold)
        self.min_rms = min_rms
        self.start_frames = max(1, start_frames)
        self.barge_min_rms = max(barge_min_rms, self.min_rms)
        self.barge_start_frames = max(barge_start_frames, self.start_frames)
        self.silence_frames = max(1, round(silence_ms * 16 / FRAME_SAMPLES))
        self.reset()

    def reset(self):
        self.state = np.zeros((2, 1, 128), dtype=np.float32)
        # Silero's streaming ONNX wrapper prepends the previous 64 samples to
        # each 512-sample frame. Without this context the model under-detects
        # speech and often stays below the configured threshold.
        self.context = np.zeros((1, 64), dtype=np.float32)
        self.pending = bytearray()
        self.active = False
        self.silent = 0
        self.candidate_frames = 0
        self.pre_roll = deque(maxlen=8)
        self.audio = bytearray()
        self.last_probability = 0.0
        self.last_rms = 0.0

    def _probability(self, pcm: bytes) -> float:
        samples = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
        feeds = {}
        for name, spec in self.inputs.items():
            if name == "input":
                model_input = np.concatenate((self.context, samples.reshape(1, -1)), axis=1)
                feeds[name] = model_input
            elif name == "state":
                feeds[name] = self.state
            elif name == "sr":
                feeds[name] = np.asarray(16000, dtype=np.int64)
            else:
                # Support compatible Silero exports with additional scalar inputs.
                shape = [int(d) if isinstance(d, int) else 1 for d in spec.shape]
                feeds[name] = np.zeros(shape, dtype=np.float32)
        result = self.session.run(None, feeds)
        if len(result) > 1 and result[1].shape == self.state.shape:
            self.state = result[1]
        self.context = model_input[:, -64:]
        return float(np.asarray(result[0]).reshape(-1)[0])

    def process(self, chunk: bytes, *, during_playback: bool = False) -> tuple[bool, bytes | None]:
        """Return (speech_started, completed_utterance_pcm)."""
        self.pending.extend(chunk)
        samples = np.frombuffer(chunk, dtype="<i2").astype(np.float32) / 32768.0
        self.last_rms = float(np.sqrt(np.mean(samples * samples))) if samples.size else 0.0
        started, completed = False, None
        max_probability = 0.0
        start_threshold = self.barge_threshold if during_playback else self.threshold
        required_start_frames = self.barge_start_frames if during_playback else self.start_frames
        required_rms = self.barge_min_rms if during_playback else self.min_rms
        frame_bytes = FRAME_SAMPLES * 2
        while len(self.pending) >= frame_bytes:
            frame = bytes(self.pending[:frame_bytes])
            del self.pending[:frame_bytes]
            probability = self._probability(frame)
            max_probability = max(max_probability, probability)
            frame_samples = np.frombuffer(frame, dtype="<i2").astype(np.float32) / 32768.0
            frame_rms = float(np.sqrt(np.mean(frame_samples * frame_samples)))
            if not self.active:
                self.pre_roll.append(frame)
                if probability >= start_threshold and frame_rms >= required_rms:
                    self.candidate_frames += 1
                    if self.candidate_frames >= required_start_frames:
                        self.active = started = True
                        self.audio = bytearray(b"".join(self.pre_roll))
                        self.silent = 0
                        self.candidate_frames = 0
                else:
                    self.candidate_frames = 0
            else:
                self.audio.extend(frame)
                if probability >= self.continuation_threshold and frame_rms >= self.min_rms:
                    self.silent = 0
                else:
                    self.silent += 1
                if self.silent >= self.silence_frames:
                    completed = bytes(self.audio)
                    self.active = False
                    self.silent = 0
                    self.audio.clear()
                    self.pre_roll.clear()
        self.last_probability = max_probability
        return started, completed
