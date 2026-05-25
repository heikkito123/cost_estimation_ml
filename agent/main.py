import json
from pathlib import Path

import ollama

from context import AgentContext
from agent import SYSTEM_PROMPT
from tools import TOOLS, list_files, read_pdf_file, read_text_file, find_file_or_dir

MODEL = "gemma4:e4b"

TOOL_REGISTRY = {
    "list_files": list_files,
    "read_text_file": read_text_file,
    "read_pdf_file": read_pdf_file,
    "find_file_or_dir": find_file_or_dir,
}

def run_agent(ctx: AgentContext, user_message: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    while True:
        stream = ollama.chat(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            stream=True,
            options={
                "num_ctx": 131000,
            },
        )

        message = {
            "role": "assistant",
            "content": "",
        }

        for chunk in stream:
            chunk_msg = chunk.get("message", {})

            if "content" in chunk_msg:
                text = chunk_msg["content"]
                message["content"] += text
                print(text, end="", flush=True)

            if "tool_calls" in chunk_msg:
                message["tool_calls"] = chunk_msg["tool_calls"]
        
        print()

        messages.append(message)

        tool_calls = message.get("tool_calls", [])

        if not tool_calls:
            return message.get("content", "")
        
        for call in tool_calls:
            function = call["function"]
            tool_name = function["name"]
            arguments = function.get("arguments", {})

            if isinstance(arguments, str):
                arguments = json.loads(arguments)
            
            tool_func = TOOL_REGISTRY.get(tool_name)

            if tool_func is None:
                result = f"Unknown tool: {tool_name}"
            else:
                result = tool_func(ctx, **arguments)
            
            messages.append(
                {
                    "role": "tool",
                    "content": result,
                    "tool_name": tool_name,
                }
            )

if __name__ == "__main__":
    root = Path("../").resolve()

    ctx = AgentContext(
        project_root=root,
        memory_file=None,
        allowed_dirs=[root],
    )

    print("Local agent ready. Type 'exit' to quit.\n")

    while True:
        user = input("You: ")

        if user.lower() in {"exit", "quit"}:
            break
        
        print("\nAgent: ", end="", flush=True)
        run_agent(ctx, user)
        print()
