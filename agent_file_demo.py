import asyncio
from pathlib import Path
from typing import Any
from dataclasses import dataclass

import pandas as pd

from agents import Agent, Runner, RunContextWrapper, function_tool

"""
General testing on openAI agents SDK.

Not really viable on small company context, technical and financial intercept
is fair when tools are refined though.
"""

@dataclass
class ProjectContext:
    project_root: Path

def safe_path(base_path, relative_path: str) -> Path:
    """
    Resolve a path inside PROJECT_ROOT to prevent escaping with ../../ tricks
    """
    full_path = (base_path / relative_path).resolve()
    if base_path.resolve() not in full_path.parents and full_path != base_path.resolve():
        raise ValueError("Access outside of project root is not allowed.")
    
    return full_path

@function_tool
def list_files(ctx: RunContextWrapper[ProjectContext], directory: str = ".") -> str:
    """
    List file in a project directory
    
    Args:
        directory: Directory inside the project folder to list.
    """
    base_path = ctx.context.project_root
    target = safe_path(base_path, directory)

    if not target.exists():
        return f"Directory '{directory}' does not exist."
    
    if not target.is_dir():
        return f"Not a directory: '{directory}'."
    
    lines = []

    for path in sorted(target.iterdir()):
        kind = "dir" if path.is_dir() else "file"
        rel = path.relative_to(base_path)
        lines.append(f'{kind}: {rel}')

    return "\n".join(lines)

@function_tool
def read_file(ctx: RunContextWrapper[ProjectContext], file_path: str) -> str:
    """
    Read a file from the project directory
    
    Args:
        file_path: Path to the file inside the project folder.
    """
    base_path = ctx.context.project_root
    target = safe_path(base_path, file_path)

    if not target.exists():
        return f"File '{file_path}' does not exist."
    
    
    if not target.is_file():
        return f"Not a file: '{file_path}'."
    
    return target.read_text(encoding="utf-8", errors="replace")

@function_tool
# TODO: note to self, do NOT mindlessly push full excel files to llm-api, it will cost an
# arm and a leg.
def read_excel_file(ctx: RunContextWrapper[ProjectContext], file_path:str) -> list[dict]:
    """
    Read an Excel file from the project directory and return its contents as a string.
    
    Args:
        file_path: Path to the Excel file inside the project folder.
    """
    base_path = ctx.context.project_root
    try:
        file = pd.read_excel(safe_path(base_path, file_path), sheet_name='Eritelysivu')
    except Exception as e:
        return f"Error reading Excel file '{file_path}': {str(e)}"
    return file.to_dict(orient='records')


@function_tool
def search_for_file(ctx: RunContextWrapper[ProjectContext], filename: str) -> str:
    """
    Search for a file by name in the project directory and its subdirectories.
    
    Args:
        filename: Name of the file to search for.
    """
    base_path = ctx.context.project_root
    matches = []

    for path in base_path.rglob(filename):
        if path.is_file():
            rel = path.relative_to(base_path)
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
    context = ProjectContext(
        project_root=Path(__file__).resolve().parent / "projektit"
    )

    result = await Runner.run(agent, user_input, context=context)

    print("\nAgent: ")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())