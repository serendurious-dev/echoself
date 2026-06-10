# Contributing to EchoSelf

Thank you for wanting to build this with us. EchoSelf accepts two kinds of contributions, and
they live under different licenses on purpose:

| Contribution type | Where it lives | License |
|---|---|---|
| Engine code (Python) | `core/`, `character/`, `learning/`, `ml/`, `visual/`, `audio/` | MIT |
| Creative content (JSON packs, sentences) | `characters/`, `lessons/`, `arcs/`, `exchange/` | CC BY 4.0 |

By submitting a pull request you agree your contribution is licensed accordingly. You retain
your copyright; content contributors are always credited (that's what the BY means).

## The Workflow

1. **Open an issue first** for anything non-trivial — bug, feature, or content pack proposal.
   Use the issue templates.
2. **Fork** the repository and create a branch from `main`:
   `git checkout -b feature/your-feature` or `content/your-pack-name`
3. **Make your changes.** One logical change per pull request.
4. **Open a pull request** using the PR template. Link the issue it resolves.
5. A maintainer reviews, discusses if needed, and merges.

## Contributing Code

- Python 3.10+, follow [PEP 8](https://peps.python.org/pep-0008/).
- Match the existing module structure — engine logic stays out of content directories.
- Docstrings on every public module, class, and function.
- **Respect the philosophy: presence over pressure.** Features that shame, pressure, streak-guilt,
  or gamify the user against their own well-being will not be merged, no matter how well written.
- The user's private data (`data/`, the Vault) is sacred. Code that transmits, analyzes Vault
  contents, or phones home will not be merged.

## Contributing Content Packs

### Personality Packs (`characters/*.json`)

A personality pack defines who a character starts as — their voice, teaching style, and visual
defaults. See [`characters/gentle_guide.json`](characters/gentle_guide.json) for the canonical
format. A pack must include:

- `id`, `name`, `archetype` — identity
- `voice` — tone descriptors and phrase banks (greeting, correct, incorrect, hesitation,
  encouragement, farewell). Write phrases that sound like a person, not a UI.
- `teaching_style` — pacing, challenge appetite, explanation depth
- `visual` — default palette, glow, form parameters for the procedural renderer
- `author` — your name or handle, for attribution

### Lesson Packs (`lessons/<track>/*.json`)

Lessons teach one concept each, in a voice-neutral template the character's current personality
colors at runtime. See [`lessons/python/example_lesson.json`](lessons/python/example_lesson.json).
A lesson must include concept, explanation, code example, quiz, and hints (exactly three,
progressively more revealing).

### Narrative Arc Packs (`arcs/*.json`)

Story chapters (7–14 sessions) selected by mood and Echo Distance. Format documented in
`arcs/README.md` as the narrative engine lands.

### Echo Exchange Sentences (`exchange/sentences.json`)

One sentence: something your ideal self told you that helped. Anonymous by default — attribution
goes in the PR history, not the sentence. Submissions must be original, kind, and free of
identifying information. No advice-giving, no toxicity, no "just try harder."

## Content Review Standards

Content PRs are reviewed for tone as much as correctness. EchoSelf speaks to people on their
worst days. Anything that could shame a struggling user — even accidentally, even as a joke —
gets a revision request, kindly.

## Questions

Open a discussion or an issue. There are no stupid questions here; that's rather the point of
the whole project.
