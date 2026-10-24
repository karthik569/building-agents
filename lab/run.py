#!/usr/bin/env python3
"""Run the same task through the loop and print a readable trace.

    python3 lab/run.py --task "Summarise what is in this directory"
    python3 lab/run.py --live --task "..."     # hit a real model (needs OPENAI_API_KEY)

Offline by default. That is deliberate: you should be able to watch the loop
do work on a plane, and you should never be tempted to hand-test instead of
writing a test.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agentlab import (  # noqa: E402
    OpenAIModel,
    ScriptedModel,
    format_trace,
    run_agent,
    starter_registry,
)

SANDBOX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sandbox")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default="Summarise what is in this directory. Read the most relevant file.")
    ap.add_argument("--root", default=SANDBOX, help="directory the agent may inspect")
    ap.add_argument("--steps", type=int, default=8, help="hard step cap")
    ap.add_argument("--live", action="store_true", help="use a real model instead of the scripted one")
    ap.add_argument("--verbose", "-v", action="store_true", help="print each event as it happens")
    args = ap.parse_args()

    if not os.path.isdir(args.root):
        print(f"no such directory: {args.root}", file=sys.stderr)
        return 2

    model = OpenAIModel() if args.live else ScriptedModel(root=args.root)

    def show(event):
        if args.verbose:
            print(f"  event {event.step:>2} {event.kind}", file=sys.stderr)

    run = run_agent(args.task, model, starter_registry(), max_steps=args.steps, on_event=show)
    print(format_trace(run))

    # The two fields you will reach for first in every debugging session.
    print(f"\nconversation messages: {len(run.messages)}")
    print(f"tool results in context: {sum(1 for m in run.messages if m.role == 'tool')}")
    return 0 if run.status == "done" else 1


if __name__ == "__main__":
    raise SystemExit(main())
