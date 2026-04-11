from __future__ import annotations

import os
import re
from pathlib import Path


DEFAULT_VOICE_MAP = {
    "narrator": "en-GB-RyanNeural",
    "character_male": "en-US-GuyNeural",
    "character_female": "en-US-JennyNeural",
}

DEFAULT_SOUND_EFFECTS = [
    "thunder",
    "rain",
    "crowd",
    "suspense_sting",
    "heartbeat",
    "wind",
    "applause",
    "door_creak",
    "footsteps",
    "dramatic_chord",
]


def clean_text(text: str) -> str:
    if text is None:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\t\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ ]{2,}", " ", text)
    return text.strip()


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or ""))


def parse_pause_seconds(pause_spec: str) -> float:
    value = pause_spec.strip().lower().replace("seconds", "s").replace("second", "s")
    match = re.search(r"([0-9]*\.?[0-9]+)\s*s", value)
    if match:
        return max(float(match.group(1)), 0.0)
    try:
        return max(float(value), 0.0)
    except ValueError:
        return 1.0


def ensure_dir(path: Path | str) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def friendly_exception(exc: Exception) -> str:
    message = str(exc).strip() or exc.__class__.__name__
    return f"{exc.__class__.__name__}: {message}"
