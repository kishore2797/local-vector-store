import io
from pathlib import Path
from typing import Optional

import chardet


def parse_file(file_content: bytes, filename: str) -> dict:
    """Parse uploaded file and extract text + metadata."""
    ext = Path(filename).suffix.lower()

    parsers = {
        ".txt": _parse_txt,
        ".md": _parse_markdown,
        ".pdf": _parse_pdf,
        ".docx": _parse_docx,
    }

    parser = parsers.get(ext)
    if not parser:
        raise ValueError(f"Unsupported file format: {ext}. Supported: {list(parsers.keys())}")

    text, metadata = parser(file_content, filename)

    metadata["filename"] = filename
    metadata["format"] = ext.lstrip(".")
    metadata["char_count"] = len(text)
    metadata["word_count"] = len(text.split())

    return {"text": text, "metadata": metadata}


def _parse_txt(content: bytes, filename: str) -> tuple[str, dict]:
    """Parse plain text with encoding detection."""
    detected = chardet.detect(content)
    encoding = detected.get("encoding", "utf-8") or "utf-8"

    text = content.decode(encoding, errors="replace")
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Strip BOM
    if text.startswith("\ufeff"):
        text = text[1:]

    metadata = {
        "encoding": encoding,
        "line_count": text.count("\n") + 1,
    }
    return text, metadata


def _parse_markdown(content: bytes, filename: str) -> tuple[str, dict]:
    """Parse Markdown file, extracting frontmatter if present."""
    text, base_meta = _parse_txt(content, filename)

    metadata = {**base_meta}

    # Extract YAML frontmatter
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1].strip()
            text = parts[2].strip()
            metadata["has_frontmatter"] = True
            # Simple key-value extraction from frontmatter
            for line in frontmatter.split("\n"):
                if ":" in line:
                    key, _, value = line.partition(":")
                    metadata[f"fm_{key.strip()}"] = value.strip()

    return text, metadata


def _parse_pdf(content: bytes, filename: str) -> tuple[str, dict]:
    """Parse PDF using PyPDF2."""
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        raise ImportError("PyPDF2 is required for PDF parsing. Install with: pip install PyPDF2")

    reader = PdfReader(io.BytesIO(content))

    pages_text = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        pages_text.append(page_text)

    text = "\n\n".join(pages_text)

    metadata = {
        "page_count": len(reader.pages),
    }

    # Extract PDF metadata
    pdf_meta = reader.metadata
    if pdf_meta:
        if pdf_meta.title:
            metadata["title"] = pdf_meta.title
        if pdf_meta.author:
            metadata["author"] = pdf_meta.author
        if pdf_meta.creation_date:
            metadata["created_date"] = str(pdf_meta.creation_date)

    return text, metadata


def _parse_docx(content: bytes, filename: str) -> tuple[str, dict]:
    """Parse DOCX using python-docx."""
    try:
        from docx import Document
    except ImportError:
        raise ImportError("python-docx is required for DOCX parsing. Install with: pip install python-docx")

    doc = Document(io.BytesIO(content))

    paragraphs = []
    for para in doc.paragraphs:
        if para.text.strip():
            paragraphs.append(para.text)

    text = "\n\n".join(paragraphs)

    metadata = {
        "paragraph_count": len(paragraphs),
    }

    # Extract DOCX metadata
    core = doc.core_properties
    if core.title:
        metadata["title"] = core.title
    if core.author:
        metadata["author"] = core.author
    if core.created:
        metadata["created_date"] = str(core.created)

    return text, metadata
