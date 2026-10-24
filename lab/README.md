# lab/ — the agent, by hand

The code for lesson 01. Stdlib only; no `pip install`.

If you have not read the lesson yet, do that first:
[`../lessons/0001-the-loop-is-the-agent.html`](../lessons/0001-the-loop-is-the-agent.html)

---

## 60-second tour

```bash
cd lab

python3 run.py --task "Summarise the release checklist"
python3 -m unittest discover -s tests -t . -v
```

The first command runs a real three-step agent loop and prints a trace. The second
runs twelve assertions in about 30 milliseconds. Neither touches the network.

---

## Two implementations, deliberately

### `minimal.py` — read this first

One file, no imports from `agentlab`. The entire agent: three tools, a model call,
and the loop. 175 lines, most of it tool definitions.

```bash
python3 minimal.py "Summarise the release checklist in lab/sandbox"
```

Requires `OPENAI_API_KEY`. It is the shortest honest answer to "what is an agent",
and the file to read if you read nothing else.

### `agentlab/` — the version with tests

The same loop, structured so it can be tested and debugged:

```
types.py    Message, Turn, ToolCall, Run, Event
tools.py    ToolRegistry, ToolError, read_file, list_files
models.py   Model protocol, ScriptedModel, OpenAIModel
loop.py     run_agent(), format_trace()
```

Use this one when you care about correctness. Use `minimal.py` when you want to see
the shape without the scaffolding.

---

## Running a task

```bash
python3 run.py                                     # default task
python3 run.py --task "..."                        # your task
python3 run.py --root /tmp/dir                     # inspect another directory
python3 run.py --steps 3                           # tighter step budget
python3 run.py --verbose                           # events printed live
python3 run.py --live                              # use a real model
```

Exit codes: `0` finished, `1` hit the step cap, `2` bad arguments.

### Sample output

```
TASK  Summarise the release checklist
STATUS done  STEPS 3
--------------------------------------------------------------------
[1] model   (no text)  0ms
          -> list_files({"path": "$REPO/lab/sandbox"})
[1] tool     list_files => notes.txt\nrelease-checklist.txt
[2] model   (no text)  0ms
          -> read_file({"path": "$REPO/lab/sandbox/release-checklist.txt"})
[2] tool     read_file => Release checklist — Q3\n============...
[3] model   Done. Saw 2 file(s). First lines: Release checklist...
[3] stop    final_answer
--------------------------------------------------------------------
FINAL Done. Saw 2 file(s). First lines: Release checklist — Q3 / ======================
```

Read the trace vertically. Each `[n]` is one step: a model turn, then the tools it
requested, then their results. `ERR` marks a tool error. `stop` says why the loop
ended.

---

## Live model setup

```bash
export OPENAI_API_KEY=sk-...
export AGENT_MODEL=gpt-4o-mini                      # optional
export OPENAI_BASE_URL=https://api.openai.com/v1    # optional
python3 run.py --live --task "..."
```

`OpenAIModel` speaks only `/v1/chat/completions`, so it works with OpenAI, Groq,
Together, vLLM, Ollama's OpenAI-compatible endpoint, or an internal gateway.

**Verified status:** the offline path is fully tested here. The live path has not
been executed in this workspace (no model credit), so treat it as syntax-checked
rather than proven. If it fails, the error will be from your provider — check the
base URL and model name first.

---

## Tests

```bash
python3 -m unittest discover -s tests -t . -v
```

Twelve tests, no network, no fixtures. They fall into three groups:

**Loop mechanics** — a single final turn stops immediately; tool results are
appended with a matching `id`; the step cap terminates a looping agent; an unknown
tool and a throwing tool both become content rather than exceptions; relative paths
are rejected; bad arguments are recoverable.

**Loop properties** — context grows monotonically; the system prompt is always
first; every trace event carries a step number.

**Scripted model behaviour** — it explores before reading, and it reads the
task-relevant file rather than the first one it saw.

### Writing your own test

Use `ReplayModel` from the test file to script exact turns:

```python
from agentlab import Turn, ToolCall, run_agent, starter_registry

model = ReplayModel([
    Turn(tool_calls=[ToolCall(id="c1", name="list_files", args={"path": "/tmp"})]),
    Turn(text="done"),
])
run = run_agent("task", model, starter_registry())
```

This tests *the loop*, not the model's judgement. For judgement, use a scripted
model or a real one and assert on the trace.

---

## Design notes

**Why `ScriptedModel` instead of a mock?** A mock asserts a call sequence and breaks
on any prompt change. The scripted model asserts behaviour over the conversation.
It also keeps the whole course offline and free. See the root README for the longer
version.

**Why do errors come back as strings?** Because the model can then read them and
change approach on the next turn. Raising kills the run; retrying identically
reproduces the failure.

**Why is `ToolError` separate from other exceptions?** Expected failures (bad path)
deserve a clean message. Unexpected ones are your bug and are labelled as such.
Both stay contained, but only one should page you.

**Why absolute paths only?** Remove the failure mode instead of documenting it.
The error hands back the absolute path so the next turn can succeed.

**Why a step cap?** Without one, a confused model is an unbounded bill.

---

## Extending it

Add a tool:

```python
from agentlab import Tool, ToolError

def word_count(path: str) -> str:
    if not path.startswith("/"):
        raise ToolError(f"path must be absolute, got {path!r}")
    with open(path) as f:
        return str(len(f.read().split()))

registry = starter_registry()
registry.register(Tool(
    name="word_count",
    description="Count words in a text file. Use for length questions. Absolute paths only.",
    input_schema={
        "type": "object",
        "properties": {"path": {"type": "string", "description": "Absolute file path."}},
        "required": ["path"],
    },
    fn=word_count,
))
```

Then write a test that asserts the model *chooses* it for a length question. If you
only test that it runs, you have tested the wrong thing.

Every new tool is a new way for the agent to fail. Add tools against a failing
trace, not because they might be useful.
