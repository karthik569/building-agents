# Building Agents — a hands-on course

Learn to build a production AI agent by writing the loop yourself. No framework.
No `pip install`. Runs offline and free.

**Start here:** [`lessons/0001-the-loop-is-the-agent.html`](lessons/0001-the-loop-is-the-agent.html)

---

## What this is

A teaching workspace, not a library. The output is your understanding, and the
artefacts are designed to be read and re-run, not imported.

- **One lesson, complete.** The agent loop, built and broken four ways.
- **A working lab.** Real code, real tests, runs in milliseconds.
- **A reference card.** One page, prints clean, for before design reviews.
- **A glossary.** Fixed vocabulary, so you and I mean the same thing.

---

## Quick start

No installation. Python 3.10+ and nothing else — everything is stdlib.

```bash
git clone <this-repo> && cd building-agents

# 1. Read the lesson (20 min)
xdg-open lessons/0001-the-loop-is-the-agent.html

# 2. Watch the loop run — offline, free, deterministic
cd lab
python3 run.py --task "Summarise the release checklist"

# 3. Run the tests — 12 assertions, ~30ms
python3 -m unittest discover -s tests -t . -v
```

That whole sequence is the first session. No API key, no signup, no cost.

Prefer to run tests from the repo root? `python3 -m unittest discover -s lab/tests -t lab`.

### Using a real model

The lab defaults to a scripted model so you can work offline. To use a real one:

```bash
export OPENAI_API_KEY=sk-...
export AGENT_MODEL=gpt-4o-mini                  # optional
export OPENAI_BASE_URL=https://api.openai.com/v1  # optional; any compatible endpoint

cd lab
python3 run.py --live --task "Summarise the release checklist"
```

`--live` swaps the model. No other code changes — that is the point of the `Model`
protocol. Works against OpenAI, Groq, Together, vLLM, Ollama's compat endpoint, or
an internal gateway, because it only uses `/v1/chat/completions`.

**Never commit a key.** If you set these in a shell for a session, fine; don't put
them in a file that gets committed.

---

## The three files to read, in order

| File | Lines | Why read it |
|---|---:|---|
| [`lab/minimal.py`](lab/minimal.py) | 175 | The whole agent in one file. Start here. |
| [`lab/agentlab/loop.py`](lab/agentlab/loop.py) | 155 | The same loop, tested, with traces and typed errors. |
| [`lab/tests/test_loop.py`](lab/tests/test_loop.py) | 177 | What "reliable" means, written as assertions. |

Everything else in `lab/agentlab/` supports those three:

| File | Role |
|---|---|
| `types.py` | `Message`, `Turn`, `ToolCall`, `Run` — the data model. |
| `tools.py` | Registry, typed `ToolError`, the starter toolset. |
| `models.py` | `ScriptedModel` (offline, rule-driven) and `OpenAIModel` (real). |

---

## Directory map

```
building-agents/            ← repo root. Everything lives here.
MISSION.md                  Why you are learning this. Grounds every lesson.
RESOURCES.md                Curated sources + communities. High-trust only.
GLOSSARY.md                 Fixed vocabulary. Lessons adhere to it.
NOTES.md                    Your preferences and my working notes.
README.md                   This file.
LICENSE                     MIT.

lessons/                    One self-contained HTML file per lesson.
  0001-the-loop-is-the-agent.html

reference/                  Printable cheat sheets. Revisit these, not the lessons.
  agent-loop.html

learning-records/           What you have demonstrably learned, and when.
  0001-prior-knowledge-and-mission.md

assets/                     Shared components. Reuse, don't fork.
  lesson.css                All styling. Every lesson links it.
  quiz.js                   Retrieval-practice widget.
  reference.css             Print-first rules for reference cards.

lab/                        The code you run.
  minimal.py                One-file agent. Read first.
  run.py                    CLI: runs a task, prints a trace.
  sandbox/                  Small directory for the agent to inspect.
  agentlab/                 The tested implementation.
  tests/                    Deterministic tests. No network.
```

---

## Common tasks

```bash
cd lab

# Run the default task
python3 run.py

# Run against a different directory
python3 run.py --root /tmp/somewhere --task "What is in here?"

# Watch events as they happen
python3 run.py --verbose

# Deliberately exhaust the step budget to see a bounded failure
python3 run.py --steps 1

# Run a single test
python3 -m unittest tests.test_loop.TestLoopMechanics.test_step_cap_terminates_a_looping_agent -v
```

`run.py` exits `0` on success and `1` on `max_steps`, so it drops straight into CI.

---

## How the lab works, and why it is built this way

Three decisions will look odd if nobody explains them.

### The scripted model is not a mock

`ScriptedModel` decides by reading the conversation with rules instead of weights.
A mock asserts *"I expected exactly these calls in this order"* — it breaks on every
harmless prompt edit and proves nothing. A scripted model asserts *"given this
conversation, a competent agent would do X"*, which is the property you actually
want to hold.

It is also why every exercise here runs offline and costs nothing. You should never
be tempted to hand-test in place of writing a test.

The consequence: it is a *teaching and testing* device, not a model. It will not
generalise to new tasks. For that, use `--live`.

### Errors are returned, never raised

In `ToolRegistry.execute`, a tool failure becomes a string that goes back into the
conversation. A raised exception kills a run that was one turn from recovering; a
returned error lets the model read the failure and change approach.

`ToolError` marks expected failures (bad path, missing file). Anything else is
tagged "unexpected" because it is a bug in your code. Without that distinction you
end up sniffing strings for `"Error:"`, which works until a file is named `Error:`.

### Paths must be absolute

Not discouraged — rejected, with the absolute path handed back so the next turn can
succeed. Anthropic found models fumble relative paths after directory changes and
fixed it by requiring absolute ones. Remove the failure mode; don't document around it.

---

## Troubleshooting

**`no such directory: .../sandbox`**
Run from inside `lab/`, or pass `--root`. `run.py` resolves `sandbox/` relative to
its own location, but an explicit `--root` is taken literally.

**`ModuleNotFoundError: No module named 'agentlab'`**
`run.py` inserts its own directory onto `sys.path`. If you are importing `agentlab`
from elsewhere, run from `lab/` or set `PYTHONPATH=lab`.

**Tests fail with `Start directory is not importable`**
You are running discovery from the wrong directory. From `lab/`:
```bash
cd lab && python3 -m unittest discover -s tests -t .
```
Both flags matter when `tests/` is not importable from the working directory. From
the repo root instead, use `python3 -m unittest discover -s lab/tests -t lab`.

**`Balance is zero` / `401` / `model_not_found` on `--live`**
That is your provider, not the lab. Check `OPENAI_BASE_URL`, `AGENT_MODEL`, and that
the account has credit. The offline path never touches the network — use it while
you sort credentials out.

**The model keeps repeating the same call**
You have found a real agent bug, which is the point. Read the trace: is the error
message vague? Did you compare a full path against a basename? Lesson 01 Step 4
walks through exactly this failure.

**Lesson renders unstyled**
CSS paths are relative (`../assets/lesson.css`). Open the file from its location, or
serve the repo root:
```bash
python3 -m http.server 8080   # then /lessons/0001-the-loop-is-the-agent.html
```

---

## Status — what exists and what does not

Honest state, so you can plan around it:

| Thing | State |
|---|---|
| Lesson 01: the loop | Complete, runnable |
| Reference card: agent loop | Complete |
| Glossary, resources, mission | Complete |
| Lab + tests | Complete, 12 passing |
| `lab/minimal.py` | Syntax-checked; not run against a live model here |
| Lesson 02 (workflow vs agent) | **Not written** |
| Lessons 03+ (evals, context, deployment) | **Not written** |

The course outline implies six sessions. One exists. Lessons 02+ need the actual
task your work agent will perform — writing them against a hypothetical would
produce generic material.

---

## Conventions, if you add to this

- Every lesson is one self-contained HTML file in `lessons/`, numbered.
- Every lesson links `assets/lesson.css`. Do not inline styles that a second lesson
  would duplicate — add a class to the stylesheet instead.
- Quiz answers must be the same length, with the correct option's position varied.
  Formatting must not leak the answer.
- Facts come from `RESOURCES.md`, not from memory. Add a source before making a claim.
- Labs run offline by default. A lesson must never require a paid API call.

---

## Repo conventions

This repository is the whole course: lessons, lab, reference material, and the
teaching state (mission, glossary, learning records). Nothing lives outside it.

- `main` is always runnable. Tests pass on every commit.
- Labs run offline by default. A commit that requires a paid API call to exercise
  is a broken commit.
- Commit messages: imperative, one line of intent (`add quiz widget`, not `stuff`).

```bash
cd building-agents
python3 -m unittest discover -s lab/tests -t lab   # must pass before committing
git add -A && git commit -m "describe the change"
```
