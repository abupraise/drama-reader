from __future__ import annotations

from anthropic import Anthropic

from .utils import clean_text, word_count


SUMMARY_MODEL = "claude-sonnet-4-20250514"
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

    client = Anthropic(api_key=api_key)
    prompt = (
        "Summarise the following text to about 250-400 words while preserving the core meaning, "
        "names, facts, chronology, and emotional tone. Return only the summary.\n\n"
        f"TEXT:\n{cleaned}"
    )

    response = client.messages.create(
        model=SUMMARY_MODEL,
        max_tokens=900,
        temperature=0.3,
        system=SUMMARY_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    summary = extract_plain_text_from_anthropic_response(response)
    summary = clean_text(summary)
    if not summary:
        raise ValueError("The summarisation step returned empty content.")
    return summary, True



def extract_plain_text_from_anthropic_response(response) -> str:
    chunks = []
    for block in getattr(response, "content", []):
        if getattr(block, "type", None) == "text":
            chunks.append(block.text)
    return "\n".join(chunks).strip()
