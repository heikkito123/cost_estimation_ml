from pathlib import Path
from context import AgentContext
import unicodedata
import tiktoken
import re
import pymupdf

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

def read_pdf_file_util(file_path):
    doc = pymupdf.open(file_path)
    text = [p.get_text() for p in doc]
    text = "\n".join(text)
    text = clean_text(text)

    return text

def tail_coverage_score(source_text: str, candidate_text: str, sample_size: int = 60) -> float:
    """
    check if the model preserved the end of a parsed output.
    """
    source_words = [word.casefold() for word in source_text.split() if len(word) >= 5]
    if not source_words:
        return 1.0

    tail_words = []
    seen = set()
    for word in reversed(source_words):
        if word in seen:
            continue

        tail_words.append(word)
        seen.add(word)

        if len(tail_words) >= sample_size:
            break

    if not tail_words:
        return 1.0

    candidate_words = {word.casefold() for word in candidate_text.split()}
    matches = sum(1 for word in tail_words if word in candidate_words)

    return matches / len(tail_words)

def chunk_text_util(text: str, chunk_size: int=3000, overlap: int=150) -> dict:
    """
    Split document into token-limited chunks on whitespace boundaries.
    """
    segments = re.findall(r'\S+\s*', text)
    chunks = {}

    if not segments:
        return chunks

    current_segments = []
    current_token_lengths = []
    current_tokens = 0
    chunk_index = 0

    for segment in segments:
        segment_tokens = len(encoding.encode(segment))

        if current_segments and current_tokens + segment_tokens > chunk_size:
            chunks[f'chunk_{chunk_index}'] = "".join(current_segments).strip()
            chunk_index += 1

            overlap_segments = []
            overlap_token_lengths = []
            overlap_tokens = 0

            for existing_segment, token_length in zip(reversed(current_segments), reversed(current_token_lengths)):
                overlap_segments.insert(0, existing_segment)
                overlap_token_lengths.insert(0, token_length)
                overlap_tokens += token_length

                if overlap_tokens >= overlap:
                    break

            current_segments = overlap_segments
            current_token_lengths = overlap_token_lengths
            current_tokens = overlap_tokens

        current_segments.append(segment)
        current_token_lengths.append(segment_tokens)
        current_tokens += segment_tokens

    if current_segments:
        chunks[f'chunk_{chunk_index}'] = "".join(current_segments).strip()

    return chunks

def write_chunks_to_file(chunks: dict) -> list:
    f_names = []
    for k, v in chunks.items():
        with open(f'{k}_temp.txt', 'w', encoding='utf-8', errors='ignore') as file:
            file.write(v)
            f_names.append(file.name)

    return f_names
