"""Deterministic tests for the loop.

These run in milliseconds and cost nothing. That is the entire point: if your
agent's tests need the network, you will not run them, and if you do not run
them you are hand-testing, and hand-testing is how the 80% trap happens.

Run: python3 -m unittest discover -s lab/tests -v
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentlab import (  # noqa: E402
    Message,
    ScriptedModel,
    Tool,
    ToolCall,
    ToolRegistry,
    Turn,
    run_agent,
    starter_registry,
)

SANDBOX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sandbox")


class ReplayModel:
    """Returns a fixed sequence of turns. Useful for testing the loop itself,
    as opposed to testing a model's decisions."""

    def __init__(self, turns: list[Turn]) -> None:
        self.turns = list(turns)
        self.seen: list[list[Message]] = []

    def complete(self, messages, tools):
        self.seen.append(list(messages))
        if not self.turns:
            return Turn(text="out of script")
        return self.turns.pop(0)


class TestLoopMechanics(unittest.TestCase):
    def test_single_final_turn_stops_immediately(self):
        run = run_agent("hi", ReplayModel([Turn(text="hello")]), starter_registry())
        self.assertEqual(run.status, "done")
        self.assertEqual(run.final, "hello")
        self.assertEqual(run.steps, 1)

    def test_tool_result_is_appended_with_matching_id(self):
        target = os.path.join(SANDBOX, "notes.txt")
        model = ReplayModel(
            [
                Turn(tool_calls=[ToolCall(id="c1", name="read_file", args={"path": target})]),
                Turn(text="read it"),
            ]
        )
        run = run_agent("read notes", model, starter_registry())

        tool_msgs = [m for m in run.messages if m.role == "tool"]
        self.assertEqual(len(tool_msgs), 1)
        self.assertEqual(tool_msgs[0].tool_call_id, "c1")
        self.assertIn("Sandbox for the agent", tool_msgs[0].content)

    def test_step_cap_terminates_a_looping_agent(self):
        forever = [
            Turn(tool_calls=[ToolCall(id=f"c{i}", name="list_files", args={"path": SANDBOX})])
            for i in range(50)
        ]
        run = run_agent("loop", ReplayModel(forever), starter_registry(), max_steps=3)
        self.assertEqual(run.status, "max_steps")
        self.assertLessEqual(run.steps, 3)

    def test_unknown_tool_becomes_content_not_exception(self):
        model = ReplayModel(
            [
                Turn(tool_calls=[ToolCall(id="c1", name="delete_everything", args={})]),
                Turn(text="ok"),
            ]
        )
        run = run_agent("x", model, starter_registry())
        tool_msg = next(m for m in run.messages if m.role == "tool")
        self.assertTrue(tool_msg.content.startswith("Error:"))
        self.assertIn("delete_everything", tool_msg.content)

    def test_tool_exception_is_contained(self):
        reg = ToolRegistry()

        def explode(**kwargs):
            raise RuntimeError("boom")

        reg.register(
            Tool(
                name="explode",
                description="always fails",
                input_schema={"type": "object", "properties": {}},
                fn=explode,
            )
        )
        model = ReplayModel(
            [Turn(tool_calls=[ToolCall(id="c1", name="explode", args={})]), Turn(text="done")]
        )
        run = run_agent("x", model, reg)
        tool_msg = next(m for m in run.messages if m.role == "tool")
        self.assertIn("RuntimeError: boom", tool_msg.content)
        self.assertEqual(run.status, "done")

    def test_relative_path_is_rejected(self):
        reg = starter_registry()
        out, is_err = reg.execute(ToolCall(id="c", name="read_file", args={"path": "notes.txt"}))
        self.assertTrue(is_err)
        self.assertIn("absolute", out)

    def test_bad_arguments_are_recoverable_not_fatal(self):
        reg = starter_registry()
        out, is_err = reg.execute(ToolCall(id="c", name="read_file", args={"wrong": "x"}))
        self.assertTrue(is_err)
        self.assertIn("bad arguments", out)


class TestLoopProperties(unittest.TestCase):
    """Properties that must hold for any model, not just a scripted one."""

    def test_context_grows_monotonically(self):
        model = ReplayModel(
            [
                Turn(tool_calls=[ToolCall(id="c1", name="list_files", args={"path": SANDBOX})]),
                Turn(text="done"),
            ]
        )
        run_agent("x", model, starter_registry())
        self.assertEqual(len(model.seen), 2)
        self.assertLess(len(model.seen[0]), len(model.seen[1]))

    def test_system_prompt_is_always_first(self):
        model = ReplayModel([Turn(text="done")])
        run_agent("x", model, starter_registry())
        self.assertEqual(model.seen[0][0].role, "system")
        self.assertEqual(model.seen[0][1].role, "user")

    def test_every_event_has_a_step_number(self):
        run = run_agent("summarise", ScriptedModel(root=SANDBOX), starter_registry())
        self.assertTrue(all(e.step >= 1 for e in run.events))


class TestScriptedModel(unittest.TestCase):
    def test_explores_then_finishes(self):
        run = run_agent(
            "Summarise the release checklist",
            ScriptedModel(root=SANDBOX),
            starter_registry(),
        )
        self.assertEqual(run.status, "done")
        names = [e.detail["name"] for e in run.events if e.kind == "tool"]
        self.assertEqual(names[0], "list_files")
        self.assertIn("read_file", names)

    def test_reads_the_task_relevant_file_not_the_first(self):
        run = run_agent(
            "Summarise the release checklist",
            ScriptedModel(root=SANDBOX),
            starter_registry(),
        )
        reads = [
            e.detail["args"]["path"]
            for e in run.events
            if e.kind == "tool" and e.detail["name"] == "read_file"
        ]
        self.assertTrue(any("release-checklist" in p for p in reads), reads)


if __name__ == "__main__":
    unittest.main()
