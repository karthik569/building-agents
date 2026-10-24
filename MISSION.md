# MISSION

The mission is the reason this repo exists. Every lesson in it is scoped against this
document. If the mission changes, update this file — the lessons should follow it, not
the other way around.

## Learner profile this repo is written for

An experienced software engineer who has not built an agent before. The material assumes
comfort with Python, HTTP, the command line, and writing tests. It deliberately does not
explain programming fundamentals.

The goal is production: an agent that does real work and survives real users, real
failures, and a real budget. Not a demo. Not a notebook. A system a team can run without
the author in the room.

## Success looks like

- Defending an architecture choice: why this task is a workflow, an agent, or a single
  LLM call — and being right.
- Having built a working agent loop from scratch, with no framework, and being able to
  explain every line.
- Testing an agent deterministically, without burning API credits, and gating changes on
  those tests.
- Putting an agent in front of a colleague with a budget cap, an approval gate on writes,
  and a trace that can be read when it fails.
- Debugging a failed run from the trace alone, and naming which of context, tool design,
  or control flow caused it.

## Constraints

- Deep-dive sessions, hands-on. Building beats reading.
- Build the primitives by hand first. Frameworks come later, if at all.
- **Every lab must run offline by default.** No exercise may depend on a paid API call.
  A learner with no credit must be able to complete the whole course.

## Out of scope

- Model training and fine-tuning.
- Prompt-engineering trivia disconnected from a running system.
- Multi-agent orchestration as a starting point. It is earned, not assumed.
