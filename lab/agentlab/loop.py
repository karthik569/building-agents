"""The loop. This is the whole agent.

Everything else in this directory is in service of these ~50 lines. Read them
until the surprise is gone, because once it is gone you can never be intimidated
by an agent framework again.

Shape (12-factor, factor 8: own your control flow):

    context = [task]
    for step in range(max_steps):
        turn = model.complete(context, tools)
        context.append(turn)
        if turn.is_final: stop
        for call in turn.tool_calls:
            output = execute(call)
            context.append(output)

That is it. No planner, no executor, no graph. Those are names for variations
on this, and you should only adopt a variation when you can point at a failing
trace that this loop produced.
"""

from __future__ import annotations

import json
import time
from dataclasses import replace
from typing import Any, Callable

from .models import Model, ScriptedModel
from .tools import ToolRegistry
from .types import Event, Message, Run, ToolCall


SYSTEM_PROMPT = """\
You are an agent operating in a sandboxed directory. You have tools.

Rules:
- Prefer reading the filesystem over guessing. Never invent file contents.
- Use absolute paths. Relative paths will be rejected.
- If a tool returns an error, read it and change your approach. Do not repeat \
the identical call.
- Stop as soon as you can answer the task. Do not explore for its own sake.
- When you finish, state the answer plainly. Do not narrate your steps.
"""


def run_agent(
    task: str,
    model: Model,
    tools: ToolRegistry,
    system_prompt: str = SYSTEM_PROMPT,
    max_steps: int = 8,
    on_event: Callable[[Event], None] | None = None,
) -> Run:
    """Execute one task to completion, a step cap, or a fatal error.

    `max_steps` is not optional politeness. A loop with no cap is an unbounded
    spend. This is the cheapest guardrail you will ever ship, so ship it first.
    """
    messages: list[Message] = [
        Message(role="system", content=system_prompt),
        Message(role="user", content=task),
    ]
    events: list[Event] = []

    def emit(event: Event) -> None:
        events.append(event)
        if on_event:
            on_event(event)

    for step in range(1, max_steps + 1):
        started = time.monotonic()
        turn = model.complete(messages, tools.specs())
        elapsed_ms = int((time.monotonic() - started) * 1000)

        messages.append(
            Message(role="assistant", content=turn.text, tool_calls=turn.tool_calls)
        )
        emit(
            Event(
                step=step,
                kind="model",
                detail={
                    "text": turn.text,
                    "tool_calls": [{"name": c.name, "args": c.args} for c in turn.tool_calls],
                    "latency_ms": elapsed_ms,
                },
            )
        )

        if turn.is_final:
            emit(Event(step=step, kind="stop", detail={"reason": "final_answer"}))
            return Run(task=task, messages=messages, events=events, status="done", final=turn.text)

        # Execute every requested call. One turn may contain several.
        for call in turn.tool_calls:
            output, is_error = tools.execute(call)
            messages.append(
                Message(role="tool", content=output, tool_call_id=call.id)
            )
            emit(
                Event(
                    step=step,
                    kind="tool",
                    detail={
                        "name": call.name,
                        "args": call.args,
                        "output": output,
                        "is_error": is_error,
                    },
                )
            )

    emit(Event(step=max_steps, kind="stop", detail={"reason": "max_steps"}))
    return Run(
        task=task,
        messages=messages,
        events=events,
        status="max_steps",
        final="(stopped: step budget exhausted)",
    )


# ---------------------------------------------------------------------------
# Trace rendering. A trace you cannot read is a trace you will not read.
# ---------------------------------------------------------------------------


def format_trace(run: Run) -> str:
    out: list[str] = []
    out.append(f"TASK  {run.task}")
    out.append(f"STATUS {run.status}  STEPS {run.steps}")
    out.append("-" * 68)
    for e in run.events:
        if e.kind == "model":
            calls = e.detail["tool_calls"]
            label = ", ".join(f"{c['name']}({json.dumps(c['args'])})" for c in calls)
            text = (e.detail["text"] or "").replace("\n", " ")
            if len(text) > 70:
                text = text[:67] + "..."
            out.append(f"[{e.step}] model   {text or '(no text)'}  {e.detail['latency_ms']}ms")
            if label:
                out.append(f"          -> {label}")
        elif e.kind == "tool":
            flag = "ERR " if e.detail["is_error"] else "    "
            body = e.detail["output"].replace("\n", "\\n")
            if len(body) > 70:
                body = body[:67] + "..."
            out.append(f"[{e.step}] tool {flag}{e.detail['name']} => {body}")
        elif e.kind == "stop":
            out.append(f"[{e.step}] stop    {e.detail['reason']}")
    out.append("-" * 68)
    out.append(f"FINAL {run.final}")
    return "\n".join(out)
