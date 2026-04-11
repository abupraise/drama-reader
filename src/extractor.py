from __future__ import annotations

import io
from pathlib import Path
from typing import BinaryIO

import pdfplumber
from docx import Document

from .utils import clean_text


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx"}


def extract_text_from_upload(uploaded_file) -> str:
    """Extract clean text from a Streamlit UploadedFile."""
    filename = getattr(uploaded_file, "name", "uploaded_file")
    suffix = Path(filename).suffix.lower()
    file_bytes = uploaded_file.read()

    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {suffix}. Please use PDF, TXT, or DOCX.")

    if suffix == ".pdf":
        text = extract_text_from_pdf(io.BytesIO(file_bytes))
    elif suffix == ".docx":
        text = extract_text_from_docx(io.BytesIO(file_bytes))
    else:
        text = extract_text_from_txt(io.BytesIO(file_bytes))

    cleaned = clean_text(text)
    if not cleaned:
        raise ValueError("No readable text could be extracted from the provided input.")
    return cleaned


def extract_text_from_pdf(file_obj: BinaryIO) -> str:
    pages = []
    with pdfplumber.open(file_obj) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages.append(page_text)
    return "\n\n".join(pages)


def extract_text_from_docx(file_obj: BinaryIO) -> str:
    document = Document(file_obj)
    paragraphs = [p.text for p in document.paragraphs if p.text and p.text.strip()]
    return "\n\n".join(paragraphs)


def extract_text_from_txt(file_obj: BinaryIO) -> str:
    data = file_obj.read()
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Could not decode TXT file. Please save it as UTF-8 or plain text.")
