from __future__ import annotations

import google.generativeai as genai

from .utils import clean_text, word_count


SUMMARY_MODEL = "gemini-2.5-flash"
SUMMARY_THRESHOLD_WORDS = 500


SUMMARY_SYSTEM_PROMPT = """You summarise user-provided text for later audio dramatisation.
Preserve the main message, key names, key facts, and emotional tone.
Return only the summary text, with no commentary.
Keep it concise but faithful.
"""


def summarise_text_if_needed(text: str, api_key: str) -> tuple[str, bool]:
    cleaned = clean_text(text)
    if word_count(cleaned) <= SUMMARY_THRESHOLD_WORDS:
        return cleaned, False

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=SUMMARY_MODEL,
        system_instruction=SUMMARY_SYSTEM_PROMPT,
    )
    prompt = (
        "Summarise the following text to about 250-400 words while preserving the core meaning, "
        "names, facts, chronology, and emotional tone. Return only the summary.\n\n"
        f"TEXT:\n{cleaned}"
    )

    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0.3, "max_output_tokens": 900},
    )

    summary = extract_plain_text_from_gemini_response(response)
    summary = clean_text(summary)
    if not summary:
        raise ValueError("The summarisation step returned empty content.")
    return summary, True



def extract_plain_text_from_gemini_response(response) -> str:
    text = getattr(response, "text", None)
    if text:
        return text.strip()

    chunks = []
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", []) or []:
            part_text = getattr(part, "text", None)
            if part_text:
                chunks.append(part_text)

    return "\n".join(chunks).strip()
