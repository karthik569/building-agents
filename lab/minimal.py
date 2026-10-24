"""The whole agent. One file. No framework, no dependencies beyond stdlib.

    export OPENAI_API_KEY=...
    python3 lab/minimal.py "Summarise the release checklist"

Everything here is the real thing: a model, three tools, and the loop. The loop
is the ~12 lines in run(). The rest is just wiring.
"""

import json
import os
import sys
import urllib.request

# ---------------------------------------------------------------------------
# 1. Tools: a name, a description, a JSON schema, and a function.
#    The description is prompt text. It is how the model decides to use it.
# ---------------------------------------------------------------------------


def list_files(path: str) -> str:
    return "\n".join(sorted(os.listdir(path))) or "(empty)"


def read_file(path: str) -> str:
    if not os.path.isabs(path):
        raise ValueError(f"path must be absolute, got {path!r}")
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()[:8000]


def write_file(path: str, content: str) -> str:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"wrote {len(content)} chars to {path}"


TOOLS = [
    {
        "name": "list_files",
        "description": "List the entries in a directory. Use this first when you do not know what files exist.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Absolute directory path."}},
            "required": ["path"],
        },
        "fn": list_files,
    },
    {
        "name": "read_file",
        "description": "Read one UTF-8 text file. Requires an absolute path. Not for directories.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Absolute file path."}},
            "required": ["path"],
        },
        "fn": read_file,
    },
    {
        "name": "write_file",
        "description": "Write text to a file, creating or overwriting it. Requires an absolute path.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute file path to write."},
                "content": {"type": "string", "description": "Full new contents of the file."},
            },
            "required": ["path", "content"],
        },
        "fn": write_file,
    },
]

# ---------------------------------------------------------------------------
# 2. The model. Any OpenAI-compatible endpoint: OpenAI, Groq, vLLM, Ollama.
#    The server is stateless — it only sees the messages you send.
# ---------------------------------------------------------------------------


def call_model(messages: list[dict], tools: list[dict]) -> dict:
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    payload = {
        "model": os.environ.get("AGENT_MODEL", "gpt-4o-mini"),
        "messages": messages,
        "tools": [
            {"type": "function",
             "function": {k: t[k] for k in ("name", "description", "parameters")}}
            for t in tools
        ],
    }
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        msg = json.loads(resp.read())["choices"][0]["message"]

    return {
        "text": msg.get("content") or "",
        "tool_calls": [
            {
                "id": c["id"],
                "name": c["function"]["name"],
                "args": json.loads(c["function"]["arguments"] or "{}"),
            }
            for c in (msg.get("tool_calls") or [])
        ],
    }


# ---------------------------------------------------------------------------
# 3. The loop. This is the agent.
# ---------------------------------------------------------------------------


def run(task: str, max_steps: int = 8) -> str:
    messages = [
        {"role": "system", "content": (
            "You are an agent with tools. Use absolute paths. "
            "Never invent file contents — read them. "
            "If a tool errors, read the message and change approach. "
            "Stop as soon as you can answer, and state the answer plainly."
        )},
        {"role": "user", "content": task},
    ]
    by_name = {t["name"]: t for t in TOOLS}

    for step in range(1, max_steps + 1):
        turn = call_model(messages, TOOLS)

        # Append the assistant turn in wire format.
        if turn["tool_calls"]:
            messages.append({
                "role": "assistant",
                "content": turn["text"] or None,
                "tool_calls": [
                    {"id": c["id"], "type": "function",
                     "function": {"name": c["name"],
                                  "arguments": json.dumps(c["args"])}}
                    for c in turn["tool_calls"]
                ],
            })
        else:
            messages.append({"role": "assistant", "content": turn["text"]})

        # No tool calls = the model says it is done.
        if not turn["tool_calls"]:
            return turn["text"]

        # Otherwise run them and feed the results back.
        for call in turn["tool_calls"]:
            print(f"  [{step}] {call['name']}({json.dumps(call['args'])})", file=sys.stderr)
            try:
                output = by_name[call["name"]]["fn"](**call["args"])
            except Exception as exc:  # errors are content, never raised
                output = f"Error: {type(exc).__name__}: {exc}"
            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": output,
            })

    return "(stopped: step cap reached)"


if __name__ == "__main__":
    task = sys.argv[1] if len(sys.argv) > 1 else (
        "List the files in lab/sandbox, read the release checklist, "
        "and tell me whether we can ship."
    )
    print(run(task))
