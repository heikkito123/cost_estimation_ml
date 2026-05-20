import asyncio
from pathlib import Path
from typing import Any

import pandas as pd

from agents import Agent, Runner, RunContextWrapper, function_tool

PROJECT_ROOT = Path(__file__).resolve().parent / "projektit"

def safe_path(relative_path: str) -> Path:
    """
    Resolve a path inside PROJECT_ROOT to prevent escaping with ../../ tricks
    """
    full_path = (PROJECT_ROOT / relative_path).resolve()
    if PROJECT_ROOT.resolve() not in full_path.parents and full_path != PROJECT_ROOT.resolve():
        raise ValueError("Access outside of project root is not allowed.")
    
    return full_path

@function_tool
def list_files(ctx: RunContextWrapper[Any], directory: str = ".") -> str:
    """
    List file in a project directory
    
    Args:
        directory: Directory inside the project folder to list.
    """
    target = safe_path(directory)

    if not target.exists():
        return f"Directory '{directory}' does not exist."
    
    if not target.is_dir():
        return f"Not a directory: '{directory}'."
    
    lines = []

    for path in sorted(target.iterdir()):
        kind = "dir" if path.is_dir() else "file"
        rel = path.relative_to(PROJECT_ROOT)
        lines.append(f'{kind}: {rel}')

    return "\n".join(lines)

@function_tool
def read_file(ctx: RunContextWrapper[Any], file_path: str) -> str:
    """
    Read a file from the project directory
    
    Args:
        file_path: Path to the file inside the project folder.
    """
    target = safe_path(file_path)

    if not target.exists():
        return f"File '{file_path}' does not exist."
    
    
    if not target.is_file():
        return f"Not a file: '{file_path}'."
    
    return target.read_text(encoding="utf-8", errors="replace")

@function_tool
# TODO: note to self, do NOT mindlessly push full excel files to llm-api, it will cost an
# arm and a leg.
def read_excel_file(ctx: RunContextWrapper[Any], file_path:str) -> str:
    """
    Read an Excel file from the project directory and return its contents as a string.
    
    Args:
        file_path: Path to the Excel file inside the project folder.
    """
    try:
        file = pd.read_excel(safe_path(file_path), sheet_name='Eritelysivu')
    except Exception as e:
        return f"Error reading Excel file '{file_path}': {str(e)}"
    return file.to_dict(orient='records')


@function_tool
def search_for_file(ctx: RunContextWrapper[Any], filename: str) -> str:
    """
    Search for a file by name in the project directory and its subdirectories.
    
    Args:
        filename: Name of the file to search for.
    """
    matches = []
    for path in PROJECT_ROOT.rglob(filename):
        if path.is_file():
            rel = path.relative_to(PROJECT_ROOT)
            matches.append(str(rel))
    
    if not matches:
        return f"No files named '{filename}' found."
    
    return "Found files:\n" + "\n".join(matches)

agent = Agent(
    name="terminal assistant",
    instructions="You are a project assistant in construction projects. You can list files, "
    "read file contents, and search for files by name in the project directory. Use the provided "
    "tools to interact with the project files as needed to assist with construction project management tasks."
    "In case of errors, report a short error description to the user.",
    model="gpt-5-mini",
    tools=[list_files, read_file, search_for_file, read_excel_file],
)

async def main() -> None:
    user_input = input("You: ")
    result = await Runner.run(agent, user_input)

    print("\nAgent: ")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())