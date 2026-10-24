"""Core value types shared by the loop, the models, and the tools.

Deliberately plain: no pydantic, no framework, no magic. Every field here is
something you will need to print in a trace when a run goes wrong.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Role = Literal["system", "user", "assistant", "tool"]


@dataclass
class ToolCall:
    """A request from the model to run one of our functions.

    `id` exists because the model may ask for several calls in one turn, and
    each result has to be matched back to its request. Lose the id and the
    model cannot tell which output belongs to which argument set.
    """

    id: str
    name: str
    args: dict[str, Any]


@dataclass
class Message:
    """One entry in the conversation.

    This conversation IS the agent's entire memory. There is no hidden state
    on the provider side: every turn re-sends this whole list. Append-only
    list of dataclasses is the simplest correct model of agent memory.
    """

    role: Role
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_call_id: str | None = None

    def to_wire(self) -> dict[str, Any]:
        """Render to the OpenAI-compatible message shape."""
        if self.role == "tool":
            return {
                "role": "tool",
                "tool_call_id": self.tool_call_id,
                "content": self.content,
            }
        if self.role == "assistant" and self.tool_calls:
            return {
                "role": "assistant",
                "content": self.content or None,
                "tool_calls": [
                    {
                        "id": c.id,
                        "type": "function",
                        "function": {
                            "name": c.name,
                            "arguments": _json_dumps(c.args),
                        },
                    }
                    for c in self.tool_calls
                ],
            }
        return {"role": self.role, "content": self.content}


def _json_dumps(obj: Any) -> str:
    import json

    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


@dataclass
class Turn:
    """What a model returns for a single call."""

    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)

    @property
    def is_final(self) -> bool:
        """A turn with no tool calls means the model believes it is done."""
        return not self.tool_calls


@dataclass
class Event:
    """One observable thing that happened during a run.

    Traces are not logging. A trace is the data structure you replay to answer
    "why did it do that?" after the fact. Build it as data, not as print().
    """

    step: int
    kind: str  # "model" | "tool" | "stop"
    detail: dict[str, Any]


@dataclass
class Run:
    """The complete, replayable record of one agent execution."""

    task: str
    messages: list[Message]
    events: list[Event]
    status: Literal["done", "max_steps"]
    final: str = ""

    @property
    def steps(self) -> int:
        return len({e.step for e in self.events})
