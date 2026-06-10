# Contributing

Thanks for wanting to build this with me. There are two kinds of contributions here and
they carry different licenses, on purpose:

| What | Where it lives | License |
|---|---|---|
| Engine code (Python) | `core/`, `character/`, `learning/`, `ml/`, `visual/`, `audio/` | MIT |
| Creative content (JSON packs, sentences) | `characters/`, `lessons/`, `arcs/`, `exchange/` | CC BY 4.0 |

By opening a pull request you agree your contribution is licensed accordingly. You keep
your copyright, and content authors are always credited — that is what the BY means.

## The workflow

1. Open an issue first for anything that is not trivial. There are templates.
2. Fork, then branch from `main`: `feature/your-feature` or `content/your-pack-name`.
3. Make the change. One logical change per pull request.
4. Open the PR with the template, link the issue.
5. I review, we talk if needed, it merges.

## Code

- Python 3.10+, PEP 8, docstrings on public things.
- Engine logic stays out of the content directories.
- **Presence over pressure is a merge requirement, not a suggestion.** Anything that
  shames, guilts, streak-pressures or gamifies the user against their own well-being will
  not be merged, no matter how clean the code is.
- The user's private data is off limits. Code that transmits anything, or reads the Vault,
  will not be merged. See [SECURITY.md](SECURITY.md).

## Content packs

**Personality packs** (`characters/*.json`) — who a character starts as: voice, teaching
style, visual defaults. [`characters/gentle_guide.json`](characters/gentle_guide.json) is
the canonical format. Write phrases that sound like a person, not like UI copy. Include
your name in the `author` field, that is your credit.

**Lesson packs** (`lessons/<track>/*.json`) — one concept per lesson, voice-neutral, the
character's current personality colors it at runtime. See
[`lessons/python/example_lesson.json`](lessons/python/example_lesson.json). Every lesson
needs a concept, an explanation, a code example, a quiz, and exactly three hints that get
progressively more revealing.

**Narrative arcs** (`arcs/*.json`) — story chapters spanning 7–14 sessions, selected by
mood and Echo Distance. The format lands with the narrative engine, see `arcs/README.md`.

**Echo Exchange** (`exchange/sentences.json`) — one sentence, something your ideal self
told you that helped. Anonymous by default, your credit lives in the git history, not in
the sentence. Original work only, nothing identifying, and please — no advice, no "just
try harder". These sentences reach people on their worst days.

## How content gets reviewed

Tone matters as much as correctness here. If something could land wrong on a struggling
person, even accidentally, even as a joke, I will ask for a revision. Kindly.

## Questions

Open an issue or a discussion. There are no stupid questions here, that is rather the
point of the whole project.
