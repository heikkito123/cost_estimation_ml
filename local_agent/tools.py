from pathlib import Path
from context import AgentContext
import pymupdf
from typing import get_type_hints
import inspect
import unicodedata
import tiktoken
import ollama
import tempfile
import time

from agent import CLEANER_SYSTEM_PROMPT

from utils import (normalize_filename, 
                   repair_mojibake, 
                   find_allowed_match, 
                   resolve_allowed_path,
                   clean_text,
                   chunk_text_util,
                   write_chunks_to_file,
                   read_pdf_file_util,
                   tail_coverage_score,
                   )

def list_files(ctx: AgentContext, directory: str) -> str:
    """
    List files in allowed directories.

    Args:
        directory: directory path to list.
    """
    path = resolve_allowed_path(ctx, directory)

    if not ctx.is_allowed_path(path):
        return f"Access denied, '{path}' not in allowed paths."
    
    if not path.exists():
        return f"Path '{path}' does not exist."
    
    if not path.is_dir():
        return f"Path '{path}' is not a directory."
    
    files = []

    for item in path.iterdir():
        marker = "[DIR]" if item.is_dir() else "[FILE]"
        files.append(f"{marker} {item.name}")

    return "\n".join(files[:100])

def read_text_file(ctx: AgentContext, file_path: str) -> str:
    """
    Read a text-like file from an allowed directory.

    Args:
        file_path: Path to the file.
    """
    path = resolve_allowed_path(ctx, file_path)

    if not ctx.is_allowed_path(path):
        return f"Filepath '{path}' is not in allowed dirs."
    
    if not path.exists():
        return f"File '{path}' does not exist."
    
    if path.suffix.lower() not in {".txt", ".py", ".md", ".json", ".csv"}:
        return f"Refusing to read unsupported file type: {path.suffix}"
    
    text = path.read_text(encoding="utf-8", errors="replace")

    return text[:10000]

def read_pdf_file(ctx: AgentContext, file_path: str) -> str:
    """
    Read pdf-file from allowed directory. If file size is too large, it will be chunked to
    chunk#_temp.txt file.

    Args:
        file_path: Path to the file.

    Return values:
        file contents, temporary chunk file names
    """
    path = resolve_allowed_path(ctx, file_path)

    if not ctx.is_allowed_path(path):
        return f"Filepath '{path}' is not in allowed dirs."
    
    if not path.exists():
        return f"File '{path}' does not exist."
    
    text = read_pdf_file_util(path)

    if len(chunks := chunk_text_util(text)) > 1:
        # f_names = write_chunks_to_file(chunks)
        # f_names = ','.join(f_names)

        return f"Pdf-file was too large to read, use parse_large_pdf_file tool."

    return text

def find_file_or_dir(ctx: AgentContext, dir_file: str) -> str:
    """
    Search for a file or a directory in allowed dirs. 
    Partial names are allowed.

    Args:
        dir_file: directory or file name fragment.
    """
    pattern = f"*{dir_file}*"
    results = []

    for root in ctx.allowed_dirs:
        root = Path(root).resolve()

        if not ctx.is_allowed_path(root):
            continue

        results.extend(root.rglob(pattern))

    if not results:
        return f"No matching files or directories found for: {dir_file}"

    return "\n".join(str(item) for item in results)

def parse_large_pdf_file(ctx: AgentContext, input_file_path: str | Path, model: str="gemma4:e4b") -> str:

    path = resolve_allowed_path(ctx, input_file_path)

    if not ctx.is_allowed_path(path):
        return f"Filepath '{path}' is not in allowed dirs."
    
    if not path.exists():
        return f"File '{path}' does not exist."
    
    text = read_pdf_file_util(path)
    chunks = chunk_text_util(text)
    total = len(chunks)
    output_path = Path(__file__).with_name("parsed_agent_output.txt")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        output_files = []

        for i, (chunk_name, chunk_text) in enumerate(chunks.items(), start=1):
            start = time.perf_counter()
            print(f'Parsing {chunk_name} ({i} / {total})')
            
            messages = [
                {
                    "role": "system",
                    "content": CLEANER_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": f"""
                    Clean this extracted Finnish construction document chunk.

                    Chunk: {chunk_name}
                    Progress: {i}/{total}

                    Rules:
                    - Preserve meaningful technical content.
                    - Keep section numbers and headings.
                    - Remove page headers, footers, table-of-contents noise, and duplicated boilerplate.
                    - Do not summarize too aggressively.
                    - Do not invent.
                    - If uncertain, keep the text.

                    RAW_TEXT:
                    {chunk_text}
                    """,
                },
            ]
            response = ollama.chat(
                model=model,
                messages=messages,
                options={
                    "num_ctx": 8000,
                    "num_predict": 1500,
                    "temperature": 0.1,
                },
                keep_alive="30m",
            )

            parsed_text = response["message"]["content"].strip()

            if not parsed_text or tail_coverage_score(chunk_text, parsed_text) < 0.35:
                parsed_text = chunk_text

            out_path = temp_dir / f"{chunk_name}_parsed.md"
            out_path.write_text(
                f"<!-- {chunk_name} ({i}/{total}) -->\n\n{parsed_text}\n",
                encoding="utf-8",
            )

            output_files.append(out_path)
            print(f'Time parsing chunk: {time.perf_counter() - start:.1f}s')

        combined = []
        for file_path in output_files:
            combined.append(file_path.read_text(encoding="utf-8"))

        final_parsed_text = "\n".join(combined)
        
        output_path.write_text(final_parsed_text, encoding="utf-8")

    return f"File parsed succesfully: {output_path}"




    
def python_type_to_json(py_type):
    if py_type == "string":
        return "string"
    if py_type is int:
        return "integer"
    if py_type is float:
        return "number"
    if py_type is bool:
        return "boolean"
    if py_type is tuple:
        return "tuple"
    return "string"

def tool_schema(func):
    sig = inspect.signature(func)
    hints = get_type_hints(func)

    properties = {}
    required = []

    for name, param in sig.parameters.items():
        if name == "ctx":
            continue

        py_type = hints.get(name, str)

        properties[name] = {
            "type": python_type_to_json(py_type),
            "description": name,
        }

        if param.default is inspect.Parameter.empty:
            required.append(name)

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": inspect.getdoc(func) or "",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }

TOOLS = [
    tool_schema(list_files),
    tool_schema(read_pdf_file),
    tool_schema(read_text_file),
    tool_schema(find_file_or_dir),
    tool_schema(parse_large_pdf_file),
]