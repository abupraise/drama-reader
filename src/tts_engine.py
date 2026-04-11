from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import edge_tts

from .utils import DEFAULT_VOICE_MAP, ensure_dir


async def get_available_voices() -> list[str]:
    voices = await edge_tts.list_voices()
    names = sorted({voice.get("ShortName") for voice in voices if voice.get("ShortName")})
    return names or sorted(DEFAULT_VOICE_MAP.values())


async def generate_speech_async(text: str, voice: str, output_path: Path) -> Path:
    ensure_dir(output_path.parent)
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(str(output_path))
    return output_path


async def generate_many_segments_async(segments: list[dict], output_dir: Path) -> list[dict]:
    ensure_dir(output_dir)
    results: list[dict] = []
    for idx, segment in enumerate(segments, start=1):
        text = segment["text"].strip()
        voice_marker = segment["voice"]
        voice_name = segment["voice_name"]
        output_path = output_dir / f"speech_{idx:04d}_{voice_marker}.mp3"
        await generate_speech_async(text=text, voice=voice_name, output_path=output_path)
        results.append({**segment, "audio_path": output_path})
    return results


def run_async(coro):
    """Safely run async code from Streamlit."""
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


def get_available_voices_sync() -> list[str]:
    return run_async(get_available_voices())


def generate_many_segments_sync(segments: list[dict], output_dir: Path) -> list[dict]:
    return run_async(generate_many_segments_async(segments=segments, output_dir=output_dir))
