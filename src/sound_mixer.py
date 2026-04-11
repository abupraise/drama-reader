from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path

from pydub import AudioSegment

from .tts_engine import generate_many_segments_sync
from .utils import DEFAULT_VOICE_MAP, ensure_dir, parse_pause_seconds


TOKEN_RE = re.compile(
    r"(\[VOICE:\s*[^\]]+\]|\[SOUND:\s*[^\]]+\]|\[PAUSE:\s*[^\]]+\])",
    flags=re.IGNORECASE,
)
VOICE_RE = re.compile(r"\[VOICE:\s*([^\]]+)\]", flags=re.IGNORECASE)
SOUND_RE = re.compile(r"\[SOUND:\s*([^\]]+)\]", flags=re.IGNORECASE)
PAUSE_RE = re.compile(r"\[PAUSE:\s*([^\]]+)\]", flags=re.IGNORECASE)


def parse_script(script_text: str, voice_map: dict[str, str]) -> list[dict]:
    tokens = TOKEN_RE.split(script_text)
    events: list[dict] = []
    active_voice = "narrator"

    for token in tokens:
        chunk = token.strip()
        if not chunk:
            continue

        voice_match = VOICE_RE.fullmatch(chunk)
        if voice_match:
            requested = normalise_voice_marker(voice_match.group(1))
            active_voice = requested if requested in voice_map else "narrator"
            continue

        sound_match = SOUND_RE.fullmatch(chunk)
        if sound_match:
            sound_name = normalise_sound_name(sound_match.group(1))
            events.append({"type": "sound", "sound_name": sound_name})
            continue

        pause_match = PAUSE_RE.fullmatch(chunk)
        if pause_match:
            pause_spec = pause_match.group(1)
            events.append({"type": "pause", "seconds": parse_pause_seconds(pause_spec)})
            continue

        text_part = clean_dialogue_text(chunk)
        if text_part:
            events.append(
                {
                    "type": "speech",
                    "voice": active_voice,
                    "voice_name": voice_map.get(active_voice, DEFAULT_VOICE_MAP["narrator"]),
                    "text": text_part,
                }
            )

    return events



def create_drama_production(
    script_text: str,
    voice_map: dict[str, str],
    enabled_sounds: dict[str, bool],
    sounds_dir: Path,
    output_path: Path,
) -> tuple[Path, list[str]]:
    logs: list[str] = []
    ensure_dir(output_path.parent)

    events = parse_script(script_text, voice_map)
    if not events:
        raise ValueError("No playable events were found in the dramatised script.")

    logs.append(f"Parsed {len(events)} script events.")

    speech_segments = [event for event in events if event["type"] == "speech"]
    temp_dir = Path(tempfile.mkdtemp(prefix="dramareader_"))

    try:
        rendered_segments = generate_many_segments_sync(speech_segments, temp_dir)
        logs.append(f"Rendered {len(rendered_segments)} speech audio segments with edge-tts.")

        rendered_iter = iter(rendered_segments)
        timeline = AudioSegment.silent(duration=0)

        for event in events:
            if event["type"] == "speech":
                rendered = next(rendered_iter)
                speech_audio = AudioSegment.from_file(rendered["audio_path"], format="mp3")
                timeline += speech_audio
            elif event["type"] == "pause":
                pause_ms = int(event["seconds"] * 1000)
                timeline += AudioSegment.silent(duration=pause_ms)
                logs.append(f"Inserted pause of {event['seconds']:.2f}s.")
            elif event["type"] == "sound":
                sound_name = event["sound_name"]
                if not enabled_sounds.get(sound_name, False):
                    logs.append(f"Skipped disabled sound: {sound_name}.")
                    continue

                sound_path = find_sound_file(sounds_dir, sound_name)
                if sound_path is None:
                    logs.append(f"Skipped missing sound file: {sound_name}.")
                    continue

                sound_audio = AudioSegment.from_file(sound_path)
                sound_audio = sound_audio - 10
                timeline += sound_audio
                logs.append(f"Inserted sound effect: {sound_name}.")

        timeline.export(output_path, format="mp3")
        return output_path, logs
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)



def find_sound_file(sounds_dir: Path, sound_name: str) -> Path | None:
    candidates = [
        sounds_dir / f"{sound_name}.mp3",
        sounds_dir / f"{sound_name}.wav",
        sounds_dir / f"{sound_name}.ogg",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None



def normalise_voice_marker(marker: str) -> str:
    marker = marker.strip().lower()
    marker = marker.replace("voice:", "")
    marker = marker.replace(" ", "_")
    return marker



def normalise_sound_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")



def clean_dialogue_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
