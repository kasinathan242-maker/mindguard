import builtins
import io
import os
import tempfile

import numpy as np
import pytest
import soundfile as sf
from fastapi import FastAPI
from httpx import AsyncClient

from app.voice.router import InvalidAudioError, analyse
from tests.helpers import start_anonymous


def tone(seconds: float, rate: int = 16_000, hz: float = 180.0) -> bytes:
    t = np.arange(int(seconds * rate)) / rate
    signal = 0.3 * np.sin(2 * np.pi * hz * t)
    signal[int(rate * seconds * 0.4) : int(rate * seconds * 0.6)] = 0.0  # a pause
    buffer = io.BytesIO()
    sf.write(buffer, signal.astype("float32"), rate, format="WAV", subtype="PCM_16")
    return buffer.getvalue()


def test_features_describe_the_recording() -> None:
    features = analyse(tone(3))
    assert features.duration_s == pytest.approx(3, abs=0.05)
    assert features.pitch_median_hz == pytest.approx(180, abs=8)
    assert 0.1 < features.pause_ratio < 0.4
    assert features.experimental is True
    assert "not a measure of depression" in features.note


def test_bad_recordings_are_rejected() -> None:
    for raw, message in (
        (b"not audio", "WAV"),
        (tone(0.5), "at least one second"),
        (tone(31), "30 seconds"),
    ):
        with pytest.raises(InvalidAudioError, match=message):
            analyse(raw)


def test_audio_is_never_written_to_disk(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = tone(2)
    real_open = builtins.open

    def no_writes(file: object, mode: str = "r", *args: object, **kwargs: object) -> object:
        if any(flag in mode for flag in "wax+"):
            raise AssertionError(f"voice analysis tried to write {file!r}")
        return real_open(file, mode, *args, **kwargs)  # type: ignore[call-overload]

    def forbidden(*_: object, **__: object) -> None:
        raise AssertionError("voice analysis created a temporary file")

    monkeypatch.setattr(builtins, "open", no_writes)
    for name in ("NamedTemporaryFile", "TemporaryFile", "mkstemp", "SpooledTemporaryFile"):
        monkeypatch.setattr(tempfile, name, forbidden)
    before = set(os.listdir(tempfile.gettempdir()))
    analyse(raw)
    assert set(os.listdir(tempfile.gettempdir())) == before


async def test_endpoint_needs_flag_and_consent(app: FastAPI, client: AsyncClient) -> None:
    await start_anonymous(client, {"core": True, "voice": True})
    files = {"file": ("checkin.wav", tone(2), "audio/wav")}
    assert (await client.post("/api/v1/voice/analyze", files=files)).status_code == 404
    assert (await client.get("/api/v1/voice/status")).json() == {"enabled": False}

    app.state.settings.voice_enabled = True
    try:
        ok = await client.post("/api/v1/voice/analyze", files=files)
        assert ok.status_code == 200
        assert ok.json()["experimental"] is True
        await client.put("/api/v1/consents", json={"consents": {"voice": False}})
        assert (await client.post("/api/v1/voice/analyze", files=files)).status_code == 403
    finally:
        app.state.settings.voice_enabled = False
