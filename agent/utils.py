from pathlib import Path
from context import AgentContext
import unicodedata
import tiktoken
import re

encoding = tiktoken.encoding_for_model("gpt-4o-mini")

def normalize_filename(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()


def repair_mojibake(value: str) -> str:
    try:
        return value.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value


def find_allowed_match(ctx: AgentContext, requested: Path) -> Path | None:
    target_names = {
        normalize_filename(requested.name),
        normalize_filename(repair_mojibake(requested.name)),
    }

    matches = []

    for directory in ctx.allowed_dirs:
        for candidate in Path(directory).rglob("*"):
            if not candidate.is_file():
                continue

            if normalize_filename(candidate.name) in target_names:
                matches.append(candidate.resolve())

    if len(matches) == 1:
        return matches[0]

    return None


def resolve_allowed_path(ctx: AgentContext, raw_path: str) -> Path:
    requested = Path(raw_path)

    candidates = []

    if requested.is_absolute():
        candidates.append(requested)
    else:
        candidates.append(Path(ctx.project_root) / requested)
        candidates.extend(Path(directory) / requested for directory in ctx.allowed_dirs)
        candidates.append(requested)

    seen = set()

    for candidate in candidates:
        resolved = candidate.resolve()

        if resolved in seen:
            continue

        seen.add(resolved)

        if resolved.exists() and ctx.is_allowed_path(resolved):
            return resolved

    matched = find_allowed_match(ctx, requested)

    if matched is not None:
        return matched

    return requested.resolve()

def clean_text(text):
    """
    Clean basic job description document text.
    """
    text = unicodedata.normalize('NFKC', text)
    text = text.replace('\n', '').strip()
    text = re.sub(r'\s{2,}', ' ', text)
    text = re.sub(r'[^\w\d]{3,}', ' ', text)

    return text

def chunk_text(text, chunk_size=10000, overlap=150):
    """
    Split document into chunk_size sized chunks.
    """
    encoded_text = encoding.encode(text)
    chunks = {}
    start = 0
    i = 0
    while start < len(encoded_text):
        end = start + chunk_size
        chunk = encoding.decode(encoded_text[start:end])
        chunks[f'chunk_{i}'] = chunk
        
        start += chunk_size - overlap
        i += 1
    return chunks

def write_chunks_to_file(chunks: dict) -> list:
    f_names = []
    for k, v in chunks.items():
        with open(f'{k}_temp.txt', 'w', encoding='utf-8', errors='ignore') as file:
            file.write(v)
            f_names.append(file.name)

    return f_names
