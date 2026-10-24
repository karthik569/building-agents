# Building Agents Glossary

The canonical language for this workspace. Lessons and learning records use these
terms exactly. Definitions describe what a term *is*, not how to do it.

## Architecture

**Augmented LLM**:
An LLM given retrieval, tools, and/or memory. The building block of every agentic
system; everything else is composition and control flow.
_Avoid_: AI agent, smart model

**Workflow**:
A system where LLMs and tools are orchestrated through code paths you wrote in
advance. Predictable, testable, cheap.
_Avoid_: pipeline (too vague — justify each hop)

**Agent**:
A system where the LLM directs its own process and tool usage, deciding the next
step at runtime. Buys flexibility; costs latency, money, and predictability.
_Avoid_: autonomous agent, AI employee

**Agent loop**:
The cycle: model returns a turn → you execute requested tools → append results →
repeat until the model returns no tool calls or a cap is hit.
_Avoid_: ReAct loop (that's one prompting style, not the loop itself)

**Control flow**:
Who decides the sequence of steps. In a workflow, your code. In an agent, the model.
_Avoid_: orchestration (overloaded — say which layer)

**Turn**:
One model response. May contain text, tool calls, or both. A turn with no tool
calls is the model's claim that it is finished.
_Avoid_: iteration, cycle

**Step**:
One full loop iteration: one model turn plus execution of the tools it requested.
_Avoid_: round, hop

## Tools

**Tool**:
A name, a description, a JSON schema, and a function. The model picks it by reading
the name and description; your code runs it.
_Avoid_: function, API, action (say tool, or say which of these you mean)

**Tool call**:
A structured request from the model to run one tool with specific arguments. Carries
an `id` so the result can be matched back to it.
_Avoid_: tool use, invocation

**Tool result**:
The output of a tool call, appended to the conversation as content. Errors are
results too — they go back to the model so it can react.
_Avoid_: tool response, observation

**Tool inventory**:
The full set of tools offered to the model on a given call. Larger inventories raise
capability and lower reliability at the same time.
_Avoid_: toolbelt, toolset

**ACI (Agent-Computer Interface)**:
The design surface of your tools — names, parameters, descriptions, error messages.
The agent equivalent of a UI, and worth the same design effort.
_Avoid_: tool schema (that's only the syntactic half)

**Poka-yoke**:
Shaping a tool's arguments so that misuse is impossible rather than merely
discouraged — e.g. requiring absolute paths so the agent cannot get lost.
_Avoid_: guardrail (that's a policy control, not a shape)

## Context

**Context window**:
Everything the model sees on one call: system prompt, the whole conversation, tool
results, and tool definitions. The agent's only memory.
_Avoid_: prompt (that's one part of it)

**Context engineering**:
Deciding what enters the context window, in what form, and what is dropped. The
dominant reliability lever in an agent.
_Avoid_: prompt engineering (narrower: wording, not composition)

**Compaction**:
Replacing old turns with a shorter summary so the run can continue inside the context
window. Lossy by design; must be tested like any other transform.
_Avoid_: summarisation, pruning (say which: drop, or compress)

## Reliability

**Trace**:
The structured, replayable record of one run: every turn, tool call, result, and
stop reason. Data, not log lines.
_Avoid_: log, telemetry (both are broader and less useful)

**Step cap**:
A hard maximum on loop iterations. The cheapest guardrail; without it a loop is an
unbounded spend.
_Avoid_: timeout, limit (say what is being capped)

**Scripted model**:
A deterministic fake model that decides by rules over the conversation. Drives the
real loop offline, so tests and demos cost nothing and never flake.
_Avoid_: mock (a mock asserts call sequences; this asserts behaviour)

**Eval**:
A fixed set of tasks with pass/fail criteria, run against a version of the agent so
changes can be compared. The thing that gets you past 80% quality.
_Avoid_: benchmark (that's a third party's eval, not yours)

**80% trap**:
Shipping a demo that impresses and a system that fails, because the last 20% needs
the evals, error paths, and control flow a framework hid from you.
_Avoid_: prototype, MVP (both are legitimate; this is the failure to leave one)
