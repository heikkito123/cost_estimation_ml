from pathlib import Path
from context import AgentContext
import pymupdf
from typing import get_type_hints
import inspect
import unicodedata
import tiktoken

from utils import (normalize_filename, 
                   repair_mojibake, 
                   find_allowed_match, 
                   resolve_allowed_path,
                   clean_text,
                   chunk_text,
                   write_chunks_to_file)

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

def read_pdf_file(ctx: AgentContext, file_path: str) -> tuple:
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
    
    doc = pymupdf.open(path)
    text = [p.get_text() for p in doc]
    text = "\n".join(text)
    text = clean_text(text)

    if len(chunks := chunk_text(text)) > 1:
        f_names = write_chunks_to_file(chunks)
        f_names = ','.join(f_names)

        return f"Pdf-file was too large to read, it was split into chunks to {f_names}"

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
]