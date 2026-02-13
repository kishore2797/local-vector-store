from typing import Optional
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
)

from app.config import config


def chunk_text(
    text: str,
    strategy: Optional[str] = None,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> list[dict]:
    """Split text into chunks using the specified strategy."""
    strategy = strategy or config.chunking.default_strategy
    chunk_size = chunk_size or config.chunking.default_chunk_size
    chunk_overlap = chunk_overlap or config.chunking.default_chunk_overlap

    if strategy == "fixed":
        splitter = CharacterTextSplitter(
            separator="",
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
    elif strategy == "semantic":
        splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
    else:  # recursive (default)
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )

    chunks = splitter.split_text(text)

    result = []
    char_offset = 0
    for i, chunk in enumerate(chunks):
        start = text.find(chunk, char_offset)
        if start == -1:
            start = char_offset
        end = start + len(chunk)

        result.append({
            "text": chunk,
            "chunk_index": i,
            "char_count": len(chunk),
            "token_estimate": len(chunk) // 4,
            "start_char": start,
            "end_char": end,
        })
        char_offset = max(char_offset, start + 1)

    return result
