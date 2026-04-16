from __future__ import annotations

import google.generativeai as genai

from .summariser import extract_plain_text_from_gemini_response
from .utils import clean_text


DRAMATISATION_MODEL = "gemini-2.5-flash"

DRAMATISATION_SYSTEM_PROMPT = """You transform plain text into a dramatic audio production script.
Rules:
- Preserve the original meaning and key facts.
- Add [SOUND: name] markers at emotionally appropriate moments.
- Add [PAUSE: 1s] style markers for dramatic timing where useful.
- Add [VOICE: narrator], [VOICE: character_male], or [VOICE: character_female] before spoken sections.
- Keep the output clear and production-ready.
- Return ONLY the marked-up script and nothing else.
"""


def dramatise_text(text: str, api_key: str) -> str:
    cleaned = clean_text(text)
    if not cleaned:
        raise ValueError("Cannot dramatise empty text.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=DRAMATISATION_MODEL,
        system_instruction=DRAMATISATION_SYSTEM_PROMPT,
    )
    user_prompt = (
        "Rewrite the following text as a dramatic audio script. "
        "Use only these voice markers: [VOICE: narrator], [VOICE: character_male], [VOICE: character_female]. "
        "Use sound markers such as [SOUND: thunder], [SOUND: crowd], [SOUND: suspense_sting], [SOUND: rain], "
        "[SOUND: heartbeat], [SOUND: wind], [SOUND: applause], [SOUND: door_creak], [SOUND: footsteps], "
        "and [SOUND: dramatic_chord] only when appropriate. Include [PAUSE: Ns] markers where useful. "
        "Return only the marked-up script.\n\n"
        f"TEXT:\n{cleaned}"
    )

    response = model.generate_content(
        user_prompt,
        generation_config={"temperature": 0.7, "max_output_tokens": 1800},
    )

    script = clean_text(extract_plain_text_from_gemini_response(response))
    if not script:
        raise ValueError("The dramatisation step returned empty content.")
    return script
