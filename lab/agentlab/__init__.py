"""agentlab — a from-scratch agent loop, built to be understood.

Public surface is intentionally tiny:

    from agentlab import ScriptedModel, starter_registry, run_agent, format_trace

    run = run_agent("Summarise the files here", ScriptedModel(root="/tmp/x"), starter_registry())
    print(format_trace(run))
"""

from .loop import SYSTEM_PROMPT, format_trace, run_agent
from .models import Model, OpenAIModel, ScriptedModel
from .tools import Tool, ToolError, ToolRegistry, read_file, list_files, starter_registry
from .types import Event, Message, Run, ToolCall, Turn

__all__ = [
    "SYSTEM_PROMPT",
    "Event",
    "Message",
    "Model",
    "OpenAIModel",
    "Run",
    "ScriptedModel",
    "Tool",
    "ToolCall",
    "ToolError",
    "ToolRegistry",
    "Turn",
    "format_trace",
    "list_files",
    "read_file",
    "run_agent",
    "starter_registry",
]
