# Building Agents — Resources

## Knowledge

- [Article: "Building effective agents" — Anthropic Engineering](https://www.anthropic.com/research/building-effective-agents)
  The canonical vocabulary: augmented LLM, workflows vs agents, and the five workflow
  patterns (chaining, routing, parallelisation, orchestrator-workers, evaluator-optimizer).
  Use for: deciding *whether* to build an agent at all, and for naming a design in a review.

- [Guide: "12-Factor Agents" — Dex Horthy (HumanLayer)](https://github.com/humanlayer/12-factor-agents)
  Twelve production-oriented principles from ~100 builders: own your prompts, own your
  context window, tools are structured outputs, unify execution + business state,
  pause/resume, compact errors, small focused agents, stateless reducer.
  Use for: anything about reliability, resumability, and why frameworks stall at 80%.

- [Article: "How to Build an Agent" — Thorsten Ball (Amp)](https://ampcode.com/how-to-build-an-agent)
  A code-editing agent in <400 lines of Go, built from zero. The single best cure for the
  belief that agents require a framework. Use for: the first hands-on build, tool definition
  anatomy, and the "it's just a loop" realisation.

- [Article: "Agents" — Chip Huyen](https://huyenchip.com/2025/01/07/agents.html)
  Chapter 6 of *AI Engineering*, standalone. Tool taxonomies (read-only vs write), planning,
  reflection, and — most valuable — an explicit catalogue of agent failure modes
  (invalid tool, invalid params, wrong param values, goal failure, reflection failure).
  Use for: designing evals, and diagnosing which failure mode you are looking at.

- [Docs: Anthropic — Writing tools for agents / tool use](https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview)
  Reference for tool schemas and the agent-computer interface (ACI). Use for: parameter
  naming, descriptions, and poka-yoke-ing a tool so the model cannot misuse it.

## Wisdom (Communities)

- [12-Factor Agents Discord](https://humanlayer.dev/discord)
  Builders actively shipping LLM software; the maintainers of the guide above are present.
  Use for: architecture critique, "is this over-engineered", production war stories.

- [r/AI_Agents](https://reddit.com/r/AI_Agents)
  Mixed signal, but high volume. Use for: seeing what breaks in the wild; filter hard.

- [Latent Space Discord](https://www.latent.space/)
  AI engineering practitioners, heavy on evals and infra. Use for: eval tooling opinions
  and postmortems of shipped systems.

- Local: your own platform/infra team
  Use for: the constraints that actually bind — data access, secrets, review process,
  and who will be on call for this agent. Not a public resource, but the most
  decision-relevant one for a work deployment.

## Gaps

- No high-trust, longitudinal source yet on **agent cost modelling** (tokens per successful
  task, budget enforcement patterns). Revisit when the build reaches deployment.
- Weak coverage of **human-in-the-loop approval UX** beyond tool-call interception. Will
  need a source before the first write-action agent.
