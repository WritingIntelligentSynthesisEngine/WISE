# utils/debug_util.py
from typing import Any
from langchain_core.prompt_values import PromptValue


def debug(*values: object, end: str | None = "\n", file: Any = None, flush: bool = False) -> None:

    print(*values, end=end, file=file, flush=flush)


def debug_prompt(prompt, input_data) -> None:
    messages: PromptValue = prompt.invoke(input_data)
    for msg in messages.to_messages():
        print(f"{msg}\n\n")
    input("回车继续\n\n")
