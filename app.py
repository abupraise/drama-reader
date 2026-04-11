import os
import textwrap
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src.dramatiser import dramatise_text
from src.extractor import extract_text_from_upload
from src.sound_mixer import create_drama_production
from src.summariser import summarise_text_if_needed
from src.tts_engine import get_available_voices_sync
from src.utils import (
    DEFAULT_SOUND_EFFECTS,
    DEFAULT_VOICE_MAP,
    ensure_dir,
    friendly_exception,
    word_count,
)


load_dotenv()
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "generated"
ensure_dir(OUTPUT_DIR)

st.set_page_config(page_title="DramaReader", page_icon="🎭", layout="wide")


def init_session_state() -> None:
    defaults = {
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "available_voices": [],
        "source_text": "",
        "processed_text": "",
        "dramatised_script": "",
        "audio_path": "",
        "generation_log": [],
        "input_filename": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()

# Load voices once per session.
if not st.session_state["available_voices"]:
    try:
        st.session_state["available_voices"] = get_available_voices_sync()
    except Exception:
        st.session_state["available_voices"] = []

voice_names = st.session_state["available_voices"] or sorted(DEFAULT_VOICE_MAP.values())

with st.sidebar:
    st.title("🎭 DramaReader")
    st.caption(
        "Convert documents or pasted text into a dramatised audio production with free open-source tooling."
    )

    api_key_value = st.text_input(
        "Anthropic API key",
        type="password",
        value=st.session_state["anthropic_api_key"],
        help="Used for summarisation and script dramatisation. Stored only in this session unless set in your environment.",
    )
    st.session_state["anthropic_api_key"] = api_key_value.strip()

    st.markdown("### Voice selection")
    narrator_voice = st.selectbox(
        "Narrator voice",
        options=voice_names,
        index=voice_names.index(DEFAULT_VOICE_MAP["narrator"]) if DEFAULT_VOICE_MAP["narrator"] in voice_names else 0,
    )
    male_voice = st.selectbox(
        "Male character voice",
        options=voice_names,
        index=voice_names.index(DEFAULT_VOICE_MAP["character_male"]) if DEFAULT_VOICE_MAP["character_male"] in voice_names else 0,
    )
    female_voice = st.selectbox(
        "Female character voice",
        options=voice_names,
        index=voice_names.index(DEFAULT_VOICE_MAP["character_female"]) if DEFAULT_VOICE_MAP["character_female"] in voice_names else 0,
    )

    selected_voice_map = {
        "narrator": narrator_voice,
        "character_male": male_voice,
        "character_female": female_voice,
    }

    st.markdown("### Sound effects")
    enabled_sounds = {}
    for sound_name in DEFAULT_SOUND_EFFECTS:
        enabled_sounds[sound_name] = st.checkbox(
            sound_name.replace("_", " ").title(), value=True, key=f"sound_{sound_name}"
        )

    generate_button = st.button("Generate Drama", type="primary", use_container_width=True)


tab_input, tab_script, tab_audio = st.tabs(["Input", "Script", "Audio"])

with tab_input:
    st.subheader("Provide source content")
    uploaded_file = st.file_uploader(
        "Upload PDF, TXT, or DOCX",
        type=["pdf", "txt", "docx"],
        accept_multiple_files=False,
    )
    pasted_text = st.text_area(
        "Or paste text here",
        height=280,
        placeholder="Paste an article, story, speech, or any text you want to dramatise...",
    )

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Extract / Refresh Text", use_container_width=True):
            try:
                if uploaded_file is not None:
                    extracted = extract_text_from_upload(uploaded_file)
                    st.session_state["source_text"] = extracted
                    st.session_state["input_filename"] = uploaded_file.name
                    st.success(f"Extracted text from {uploaded_file.name}.")
                elif pasted_text.strip():
                    st.session_state["source_text"] = pasted_text.strip()
                    st.session_state["input_filename"] = "pasted_text"
                    st.success("Loaded pasted text.")
                else:
                    st.warning("Please upload a file or paste some text first.")
            except Exception as exc:
                st.error(friendly_exception(exc))

    with col_b:
        if st.button("Use pasted text now", use_container_width=True):
            if pasted_text.strip():
                st.session_state["source_text"] = pasted_text.strip()
                st.session_state["input_filename"] = "pasted_text"
                st.success("Pasted text loaded.")
            else:
                st.warning("Nothing has been pasted yet.")

    current_source = st.session_state.get("source_text", "")
    st.markdown("### Extracted text")
    edited_source = st.text_area(
        "You can edit the extracted text before processing",
        value=current_source,
        height=340,
        key="editable_source_text",
    )
    st.session_state["source_text"] = edited_source

    if current_source:
        st.info(f"Current word count: {word_count(current_source)} words")

with tab_script:
    st.subheader("Processing view")
    left, right = st.columns(2)

    with left:
        st.markdown("#### Source / processed text")
        st.text_area(
            "This is the text that will be sent to the dramatisation step",
            value=st.session_state.get("processed_text") or st.session_state.get("source_text", ""),
            height=420,
            disabled=False,
            key="processed_text_editor",
        )

    with right:
        st.markdown("#### Dramatised script")
        st.text_area(
            "Generated dramatic script",
            value=st.session_state.get("dramatised_script", ""),
            height=420,
            disabled=False,
            key="dramatic_script_editor",
        )

with tab_audio:
    st.subheader("Audio output")
    audio_path = st.session_state.get("audio_path", "")
    if audio_path and Path(audio_path).exists():
        st.audio(audio_path, format="audio/mp3")
        with open(audio_path, "rb") as f:
            st.download_button(
                "Download MP3",
                data=f.read(),
                file_name=Path(audio_path).name,
                mime="audio/mpeg",
                use_container_width=True,
            )
    else:
        st.info("No audio generated yet.")

    with st.expander("Generation log", expanded=True):
        logs = st.session_state.get("generation_log", [])
        if logs:
            st.code("\n".join(logs), language="text")
        else:
            st.write("Logs will appear here after generation.")

    with st.expander("Full dramatised script", expanded=False):
        st.text_area(
            "Script preview",
            value=st.session_state.get("dramatised_script", ""),
            height=320,
            disabled=False,
            key="dramatic_script_full_editor",
        )


if generate_button:
    try:
        source_text = st.session_state.get("source_text", "").strip()
        api_key = st.session_state.get("anthropic_api_key", "").strip()

        if not source_text:
            st.error("Please provide or extract some text before generating drama.")
            st.stop()

        if not api_key:
            st.error("Please provide your Anthropic API key in the sidebar.")
            st.stop()

        log_lines = []
        log_lines.append(f"Loaded source text with {word_count(source_text)} words.")

        with st.spinner("Summarising long text if needed..."):
            processed_text, was_summarised = summarise_text_if_needed(source_text, api_key)
            st.session_state["processed_text"] = processed_text
            if was_summarised:
                log_lines.append("Text exceeded 500 words and was summarised before dramatisation.")
            else:
                log_lines.append("Text was short enough, so no summarisation was applied.")

        with st.spinner("Creating dramatic script..."):
            dramatised_script = dramatise_text(processed_text, api_key)
            st.session_state["dramatised_script"] = dramatised_script
            log_lines.append("Dramatic script generated successfully.")

        # Allow final user edits made in tab 2 or tab 3 before audio generation.
        edited_processed_text = st.session_state.get("processed_text_editor", processed_text).strip()
        if edited_processed_text:
            st.session_state["processed_text"] = edited_processed_text

        edited_script = (
            st.session_state.get("dramatic_script_full_editor")
            or st.session_state.get("dramatic_script_editor")
            or dramatised_script
        )
        edited_script = edited_script.strip()
        st.session_state["dramatised_script"] = edited_script

        safe_stem = Path(st.session_state.get("input_filename") or "drama_reader").stem
        output_mp3 = OUTPUT_DIR / f"{safe_stem}_drama.mp3"

        with st.spinner("Generating voices and mixing audio..."):
            final_audio_path, mixer_logs = create_drama_production(
                script_text=st.session_state["dramatised_script"],
                voice_map=selected_voice_map,
                enabled_sounds=enabled_sounds,
                sounds_dir=BASE_DIR / "sounds",
                output_path=output_mp3,
            )
            log_lines.extend(mixer_logs)
            st.session_state["audio_path"] = str(final_audio_path)
            log_lines.append(f"Final MP3 written to {final_audio_path}.")

        st.session_state["generation_log"] = log_lines
        st.success("Drama production completed. Open the Audio tab to preview and download it.")

    except Exception as exc:
        previous = st.session_state.get("generation_log", [])
        previous.append(f"ERROR: {friendly_exception(exc)}")
        st.session_state["generation_log"] = previous
        st.error(friendly_exception(exc))


with st.container():
    st.markdown("---")
    st.caption(
        textwrap.dedent(
            """
            Tip: first load your text in the Input tab, optionally edit it, then click **Generate Drama** in the sidebar.
            Missing sound files are skipped automatically, so the app still works even if your sounds folder is incomplete.
            """
        ).strip()
    )
