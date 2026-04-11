# DramaReader

DramaReader is a free, open-source Streamlit app that turns documents or pasted text into a dramatised audio production with multiple voices, pauses, and optional sound effects.

## Features

- Accepts **PDF**, **TXT**, **DOCX**, or raw pasted text
- Extracts readable text from uploaded documents
- Automatically summarises long text above **500 words** using Anthropic Claude
- Rewrites source content into a marked dramatic script with:
  - `[VOICE: narrator]`
  - `[VOICE: character_male]`
  - `[VOICE: character_female]`
  - `[SOUND: thunder]`, `[SOUND: crowd]`, etc.
  - `[PAUSE: 1s]`
- Uses **edge-tts** for free human-like neural voices
- Lets users override the default voices from dynamically loaded Edge voice options
- Mixes speech, silence, and sound effects into one MP3 using **pydub** + **ffmpeg**
- Gracefully skips missing or disabled sound effects
- Provides in-app preview, script inspection, and MP3 download

## Project structure

```text
DramaReader/
├── app.py
├── requirements.txt
├── packages.txt
├── .env.example
├── README.md
├── .gitignore
├── src/
│   ├── extractor.py
│   ├── summariser.py
│   ├── dramatiser.py
│   ├── tts_engine.py
│   ├── sound_mixer.py
│   └── utils.py
└── sounds/
    └── README.md
```

## Requirements

- Python **3.10+**
- `ffmpeg` installed locally, or provided by Hugging Face Spaces through `packages.txt`
- An **Anthropic API key** for summarisation and dramatisation

## Local setup

### 1. Clone or download the project

```bash
git clone https://github.com/abupraise/drama-reader
cd DramaReader
```

### 2. Create and activate a virtual environment

#### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
```

#### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and add your Anthropic API key.

#### macOS / Linux

```bash
cp .env.example .env
```

#### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

Then edit `.env`:

```env
ANTHROPIC_API_KEY=api_key_here
```

### 5. Add sound effects

The app works even if sound files are missing, but for the full experience add the required files into `sounds/`.
See `sounds/README.md` for suggested Creative Commons sources and naming.

### 6. Run the app

```bash
streamlit run app.py
```

## How to use

1. Start the app.
2. Enter your Anthropic API key in the sidebar.
3. Upload a PDF, TXT, or DOCX file, or paste text into the input box.
4. Click **Extract / Refresh Text**.
5. Review and edit the extracted text if needed.
6. Choose the narrator and character voices.
7. Enable or disable sound effects.
8. Click **Generate Drama**.
9. Review the generated script and play or download the MP3 in the Audio tab.

## Notes on sound effects

- Sound effects are inserted **in sequence** at the point where the `[SOUND: ...]` marker appears.
- If a sound is disabled in the sidebar, it is skipped silently.
- If the file is missing from `sounds/`, it is skipped without crashing the app.
- The mixer lowers sound effects by approximately **10 dB** relative to speech.

## Hugging Face Spaces deployment

DramaReader can be deployed for free to **Hugging Face Spaces** as a Streamlit app.

### 1. Create a new Space

- Go to Hugging Face Spaces
- Create a new Space
- Choose **Streamlit** as the SDK
- Choose a public or private repository

### 2. Upload project files

Upload the full project including:

- `app.py`
- `requirements.txt`
- `packages.txt`
- `src/`
- `sounds/` (optional but recommended)

### 3. Set your secret

In the Space settings, add:

- `ANTHROPIC_API_KEY` as a repository secret

You can also leave the app to accept the key from the sidebar instead.

### 4. Ensure ffmpeg is installed

This repository already includes:

```text
packages.txt
```

with:

```text
ffmpeg
```

That allows Hugging Face to install ffmpeg at build time.

## Troubleshooting

### ffmpeg not found

If audio export fails locally, install ffmpeg.

- macOS: `brew install ffmpeg`
- Ubuntu/Debian: `sudo apt-get update && sudo apt-get install ffmpeg`
- Windows: install ffmpeg and ensure it is on your PATH

### PDF extraction returned little or no text

Some PDFs are image-based scans. This app does not perform OCR. Use a text-based PDF when possible.

### edge-tts voice listing fails

The app falls back to the default voices if dynamic voice retrieval fails.

### Anthropic errors

Check that:

- your API key is valid
- your account has access to the requested model
- your network allows outbound API calls

## License and assets

- Voice generation: performed through the free `edge-tts` package
- Sound effects: use properly attributed Creative Commons files where required

