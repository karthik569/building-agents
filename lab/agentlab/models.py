"""Models: one interface, two implementations.

`ScriptedModel` is not a mock. It is a fake model that makes decisions by reading
the conversation the same way a real model does — it just does so with rules
instead of weights. That distinction matters:

  - a mock asserts "I expected this exact call sequence", which breaks on every
    harmless prompt change and proves nothing;
  - a scripted model asserts "given this conversation, a competent agent would
    do X", which is the property you actually want to hold.

It is also the reason every lab in this course runs offline and with zero API
cost, while still exercising the real loop.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Protocol

from .types import Message, ToolCall, Turn


class Model(Protocol):
    def complete(self, messages: list[Message], tools: list[dict[str, Any]]) -> Turn: ...


# ---------------------------------------------------------------------------
# Scripted model: deterministic, offline, rule-driven.
# ---------------------------------------------------------------------------


class ScriptedModel:
    """A tiny rule-based agent stand-in.

    Rules, in priority order:
      1. If a tool result came back with an error, report it (don't loop forever).
      2. If we have not listed files yet and the task mentions a file/dir, list it.
      3. If we know about a file but have not read it, read it.
      4. Otherwise, summarise what we have and stop.

    This is enough to drive a real, multi-step tool-using run — including
    recovering from a bad path — without a network call.
    """

    def __init__(self, root: str) -> None:
        self.root = root
        self._n = 0

    def _next_id(self) -> str:
        self._n += 1
        return f"call_{self._n}"

    def complete(self, messages: list[Message], tools: list[dict[str, Any]]) -> Turn:
        available = {t["name"] for t in tools}
        task = next((m.content for m in messages if m.role == "user"), "").lower()

        # What has already happened?
        listed: list[str] = []
        read: list[str] = []
        errors: list[str] = []
        for m in messages:
            if m.role == "assistant":
                for c in m.tool_calls:
                    if c.name == "list_files":
                        listed.append(str(c.args.get("path", "")))
                    elif c.name == "read_file":
                        # Track basenames. Comparing full paths against bare
                        # filenames is how you get an infinite read loop — the
                        # set membership never matches and the model repeats.
                        read.append(os.path.basename(str(c.args.get("path", ""))))
            elif m.role == "tool" and m.content.startswith("Error:"):
                errors.append(m.content)

        # Rule 1: stop on error rather than thrash. A real model often needs the
        # same nudge, which is why errors are returned as content (factor 9).
        if errors:
            return Turn(text=f"Stopped after tool error: {errors[-1]}")

        # Rule 2: explore the working directory first.
        if "list_files" in available and not listed:
            return Turn(
                tool_calls=[
                    ToolCall(id=self._next_id(), name="list_files", args={"path": self.root})
                ]
            )

        # Rule 3: read the most task-relevant file we saw.
        seen = self._seen_files(messages)
        wanted = [f for f in seen if self._matches(f, task)]
        target = (wanted or seen or [None])[0]
        if target and "read_file" in available and target not in read:
            return Turn(
                tool_calls=[
                    ToolCall(
                        id=self._next_id(),
                        name="read_file",
                        args={"path": os.path.join(self.root, target)},
                    )
                ]
            )

        # Rule 4: finish.
        body = self._last_tool_output(messages)
        return Turn(text=f"Done. {self._summarise(seen, body)}")

    @staticmethod
    def _seen_files(messages: list[Message]) -> list[str]:
        for m in messages:
            if m.role == "tool" and "\n" in m.content and "Error:" not in m.content:
                names = [ln.rstrip("/") for ln in m.content.splitlines() if ln.strip()]
                files = [n for n in names if "." in n]
                if files:
                    return files
        return []

    @staticmethod
    def _matches(filename: str, task: str) -> bool:
        """Does this file look like the one the task is about?

        Normalise separators before comparing. 'release-checklist.txt' and
        'summarise the release checklist' are obviously the same thing to a
        human and obviously different to a string comparison — a real model
        bridges that gap with semantics, and our rules have to fake it.
        """
        stem = filename.rsplit(".", 1)[0].lower()
        norm_stem = stem.replace("-", " ").replace("_", " ")
        norm_task = task.replace("-", " ").replace("_", " ")
        if norm_stem in norm_task:
            return True
        # Also match on any distinctive word (len > 4) from the filename.
        words = [w for w in norm_stem.split() if len(w) > 4]
        return any(w in norm_task for w in words)

    @staticmethod
    def _last_tool_output(messages: list[Message]) -> str:
        for m in reversed(messages):
            if m.role == "tool":
                return m.content
        return ""

    @staticmethod
    def _summarise(seen: list[str], body: str) -> str:
        head = (body or "").strip().splitlines()[:3]
        joined = " / ".join(h.strip() for h in head if h.strip())
        return f"Saw {len(seen)} file(s). First lines: {joined}"


# ---------------------------------------------------------------------------
# Real model: OpenAI-compatible, no SDK. ~40 lines is the whole integration.
# ---------------------------------------------------------------------------


class OpenAIModel:
    """Minimal client. No SDK, so there is nothing hidden between you and the wire.

    Reads OPENAI_API_KEY / OPENAI_BASE_URL. Works against OpenAI, Together,
    Groq, vLLM, Ollama's compat endpoint, or an internal gateway — anything
    speaking /v1/chat/completions.
    """

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        temperature: float = 0.0,
        timeout: int = 90,
    ) -> None:
        self.model = model or os.environ.get("AGENT_MODEL", "gpt-4o-mini")
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.temperature = temperature
        self.timeout = timeout

    def complete(self, messages: list[Message], tools: list[dict[str, Any]]) -> Turn:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [m.to_wire() for m in messages],
            "temperature": self.temperature,
        }
        if tools:
            payload["tools"] = [{"type": "function", "function": t} for t in tools]

        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read())

        msg = data["choices"][0]["message"]
        calls = []
        for c in msg.get("tool_calls") or []:
            raw = c["function"].get("arguments") or "{}"
            try:
                args = json.loads(raw)
            except json.JSONDecodeError:
                # The model emitted unparseable JSON. Surface it as a tool error
                # rather than crashing: the model gets one chance to repair.
                args = {"__parse_error__": raw}
            calls.append(ToolCall(id=c["id"], name=c["function"]["name"], args=args))

        return Turn(text=msg.get("content") or "", tool_calls=calls)
