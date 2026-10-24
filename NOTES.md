# NOTES.md

Working notes for whoever maintains this course — design decisions, open questions, and
things worth revisiting. Not a journal.

## Design decisions

- **Build the loop before teaching when not to build one.** Lesson 01 deliberately
  constructs the agent loop first, so that the workflow-versus-agent trade-off in the
  next session lands as a judgement call rather than a rule handed down from authority.
- **Scripted models are both teaching device and testing device.** The same offline
  `ScriptedModel` powers every exercise and every test. Same artefact, two purposes.
- **Labs run offline by default.** A lesson that needs a paid API call to exercise is
  unusable for a learner without credit, and worse, it tempts hand-testing over writing
  tests.
- **The 80% trap is the emotional core.** The point of the course is shipping, not
  demoing. Every lesson should return to why the last 20% is where projects die.

## Open questions

- Lessons 02+ need a concrete agent task to be written against. Without a real target,
  material about evals and deployment is generic.
- Which providers matter most matters for the tool-schema lesson: OpenAI-compatible
  function calling is the common denominator, but Anthropic's schema differs enough to
  be worth a section.

## Conventions

- One self-contained HTML lesson per file in `lessons/`, numbered sequentially.
- Every lesson links `assets/lesson.css`. Add shared styles there rather than inlining.
- Quiz options must be equal length, with the correct answer's position varied.
- Claims cite a source from `RESOURCES.md`. Do not write from memory.
