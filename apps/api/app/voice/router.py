"""Voice check-in (experimental, behind VOICE_ENABLED and the `voice` consent).

The browser records up to 30 seconds and sends 16-bit WAV. Audio is decoded from memory, a few
prosody features are computed, and the bytes are dropped when the request ends: nothing is
written to disk or the database. The features describe how the voice sounded (pitch, loudness,
pauses, pace); they are not an emotion verdict and not a measure of depression.
"""

import io
from typing import Annotated

import numpy as np
import soundfile as sf
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from app.auth.models import User
from app.consent.deps import require_consent
from app.core.deps import SettingsDep

MAX_SECONDS = 30
MAX_BYTES = 2 * 1024 * 1024  # 30 s of 16 kHz mono 16-bit WAV is about 1 MB
TARGET_RATE = 16_000

router = APIRouter(prefix="/voice", tags=["voice"])
VoiceUser = Annotated[User, Depends(require_consent("voice"))]


class VoiceFeatures(BaseModel):
    duration_s: float
    pitch_median_hz: float | None
    pitch_variability_hz: float | None
    energy_rms: float
    pause_ratio: float
    onsets_per_second: float
    experimental: bool = True
    note: str = (
        "Experimental. These describe how your voice sounded, not how you feel, and are not a "
        "measure of depression."
    )


class InvalidAudioError(ValueError):
    pass


def analyse(raw: bytes) -> VoiceFeatures:
    """Pure function over in-memory bytes; no file or network access."""
    import librosa  # heavy import, deferred until a voice check-in actually happens

    try:
        audio, rate = sf.read(io.BytesIO(raw), dtype="float32", always_2d=True)
    except (sf.LibsndfileError, RuntimeError) as exc:
        raise InvalidAudioError("audio must be a WAV file") from exc
    mono = audio.mean(axis=1)
    duration = len(mono) / rate
    if duration < 1:
        raise InvalidAudioError("record at least one second")
    if duration > MAX_SECONDS + 0.5:
        raise InvalidAudioError(f"recordings are limited to {MAX_SECONDS} seconds")
    if rate != TARGET_RATE:
        mono = librosa.resample(mono, orig_sr=rate, target_sr=TARGET_RATE)
        rate = TARGET_RATE

    f0, voiced, _ = librosa.pyin(mono, fmin=65, fmax=400, sr=rate)
    pitches = f0[voiced & ~np.isnan(f0)]
    rms = librosa.feature.rms(y=mono)[0]
    silent = rms < max(float(np.percentile(rms, 90)) * 0.1, 1e-4)
    onsets = librosa.onset.onset_detect(y=mono, sr=rate)
    return VoiceFeatures(
        duration_s=round(duration, 2),
        pitch_median_hz=round(float(np.median(pitches)), 1) if pitches.size else None,
        pitch_variability_hz=round(float(np.std(pitches)), 1) if pitches.size else None,
        energy_rms=round(float(rms.mean()), 4),
        pause_ratio=round(float(silent.mean()), 3),
        onsets_per_second=round(len(onsets) / duration, 2),
    )


class VoiceStatus(BaseModel):
    enabled: bool


@router.get("/status")
async def voice_status(settings: SettingsDep) -> VoiceStatus:
    return VoiceStatus(enabled=settings.voice_enabled)


@router.post("/analyze")
async def analyze(file: UploadFile, user: VoiceUser, settings: SettingsDep) -> VoiceFeatures:
    if not settings.voice_enabled:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Voice check-ins are not enabled")
    raw = await file.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "Recording is too large")
    try:
        return await run_in_threadpool(analyse, raw)
    except InvalidAudioError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    finally:
        del raw
