"""Tool registry: the agent's action space.

The registry is small on purpose. Two ideas matter and both are load-bearing:

1. A tool is a name, a description, a JSON schema, and a function. Nothing else.
   (12-factor, factor 4: "tools are just structured outputs".)
2. The description is prompt text. It is the single highest-leverage string in
   the system, because the model chooses tools by reading it.
"""

from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .types import ToolCall


class ToolError(Exception):
    """Raise this for expected, recoverable failures (bad path, missing file).

    The distinction is load-bearing:
      - ToolError    -> expected. The model can fix it. Report as error content.
      - anything else -> unexpected. Still contained, but also a bug in your code.
    Without a typed error you end up sniffing strings for "Error:", which is
    exactly the kind of thing that works until someone's file is named Error:.
    """


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]
    fn: Callable[..., str]

    def spec(self) -> dict[str, Any]:
        """The OpenAI-compatible function spec."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.input_schema,
        }


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"duplicate tool name: {tool.name}")
        self._tools[tool.name] = tool

    def specs(self) -> list[dict[str, Any]]:
        return [t.spec() for t in self._tools.values()]

    def names(self) -> list[str]:
        return list(self._tools)

    def execute(self, call: ToolCall) -> tuple[str, bool]:
        """Run one call. Returns (output, is_error).

        Errors are returned as *content*, never raised. A raised exception
        destroys the run and teaches the model nothing; a returned error string
        goes back into the conversation where the model can react to it.
        """
        tool = self._tools.get(call.name)
        if tool is None:
            return (f"Error: no tool named {call.name!r}. Available: {self.names()}", True)
        try:
            return (tool.fn(**call.args), False)
        except ToolError as exc:
            return (f"Error: {exc}", True)
        except TypeError as exc:
            # Usually a wrong/missing argument from the model. Recoverable, and
            # the message should tell it what the signature actually is.
            return (f"Error: bad arguments for {call.name}: {exc}", True)
        except Exception as exc:  # noqa: BLE001 - boundary by design
            return (f"Error: unexpected {type(exc).__name__}: {exc}", True)


# ---------------------------------------------------------------------------
# The starter toolset. Note the absolute-path decision: an agent that can cd
# around will eventually pass a relative path from the wrong cwd. Forcing
# absolute paths is "poka-yoke" (Anthropic, Appendix 2) — it removes the
# failure mode rather than documenting it.
# ---------------------------------------------------------------------------


def read_file(path: str) -> str:
    p = Path(path)
    if not p.is_absolute():
        raise ToolError(f"path must be absolute, got {path!r}. Pass the full path, e.g. '{p.resolve()}'.")
    if not p.is_file():
        raise ToolError(f"not a file: {path}. Use list_files to see what exists.")
    text = p.read_text(encoding="utf-8", errors="replace")
    if len(text) > 20_000:
        return text[:20_000] + f"\n\n[truncated: file is {len(text)} chars]"
    return text


def list_files(path: str, pattern: str = "*") -> str:
    p = Path(path)
    if not p.is_absolute():
        raise ToolError(f"path must be absolute, got {path!r}.")
    if not p.is_dir():
        raise ToolError(f"not a directory: {path}. Use list_files on a parent directory.")
    entries = []
    for name in sorted(os.listdir(p)):
        full = p / name
        marker = "/" if full.is_dir() else ""
        if fnmatch.fnmatch(name, pattern):
            entries.append(f"{name}{marker}")
    return "\n".join(entries) or "(empty)"


def starter_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(
        Tool(
            name="list_files",
            description=(
                "List the entries in a directory. Use this first when you do not "
                "know what files exist. Returns one entry per line; directories "
                "end with a slash. Does not recurse and does not read contents."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path of the directory to list.",
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Optional glob to filter names, e.g. '*.py'.",
                    },
                },
                "required": ["path"],
            },
            fn=list_files,
        )
    )
    reg.register(
        Tool(
            name="read_file",
            description=(
                "Read one UTF-8 text file and return its contents. Requires an "
                "absolute path. Do not use this on directories; use list_files."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path of the file to read.",
                    }
                },
                "required": ["path"],
            },
            fn=read_file,
        )
    )
    return reg
