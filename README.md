# EchoSelf

> *"The version of you that made it — is waiting to tell you how."*

EchoSelf is an open source Python platform — a **living psychological companion and adaptive
learning system**. You build a character; the character teaches you programming, watches how you
learn, and silently becomes who you need them to be.

It is not a chatbot. It is not a productivity tracker. It is not a tutorial app.

It is a system that learns you, teaches you, and grows with you — simultaneously.

**The core philosophy: presence over pressure.** Every feature is designed so you never feel
alone, never feel shamed, and never feel pushed harder than you can handle in that moment.

---

## The Three Worlds

EchoSelf runs across three interconnected environments, unified by a continuously learning ML brain:

- **The Ambient World** — a living sky rendered in Pygame. Your character's color bleeds into the
  environment; stars drift with your Echo Distance. Drift Mode lives here: a soft place to simply
  exist, no interaction required.
- **The Learning World** — where your character teaches. A glowing panel opens beside them with
  lessons, code examples, and challenges. The world's color and atmosphere shift with your
  detected psychological state.
- **The Inner World** — invisible but constant. A behavioral model reads your patterns passively
  (response speed, pauses, session rhythm — never your private writing) and decides, without ever
  asking, whether you need a challenge or empathy, a push or silence.

## Key Features

- **Code-drawn character** — your companion is rendered 100% procedurally. No image assets exist
  in this repository; the character is source code, breathing.
- **Five pre-built personalities** — the Strict Mentor, the Gentle Guide, the Playful Rival, the
  Philosophical Elder, the Quiet Empath — or build your own from scratch.
- **Personality drift** — every session, the character drifts slightly toward what actually works
  for you. It is never announced. After thirty sessions, they have genuinely changed.
- **CodePath** — learn Python (C, C++, and Java tracks on the roadmap) through lessons taught in
  your character's voice, with real coding challenges solved in *your own editor* while the
  character runs the tests and reacts live.
- **Four-Axis Echo Distance** — the gap between who you are and who you want to be, tracked across
  Mental, Behavioral, Emotional, and Learning dimensions. Radar chart and 30-day timeline.
- **Dark Days Protocol** — when a low-mood streak is detected, all pressure stops. The narrative
  pauses. The character stays.
- **Mirror Report** — a weekly reflection written in your ideal self's voice.
- **The Vault** — a locally encrypted private writing space. Never read by the system. Just held.
- **Echo Exchange** — anonymous community sentences ("something your ideal self told you that
  helped"), contributed via pull request.

## Status

🚧 **Under active development.** This repository currently contains the project foundation
(Layer 0): structure, OSS documentation, and module skeletons. See the
[Roadmap](#roadmap) below — the build is public from the first commit, on purpose.

## Installation

```bash
git clone https://github.com/<your-username>/echoself.git
cd echoself
pip install -r requirements.txt
python main.py
```

Requires Python 3.10+.

## Usage

```bash
python main.py              # normal session
python main.py --demo       # experience EchoSelf with a lived-in profile (~35 days of history)
python main.py --timelapse  # accelerated mode: each session counts as one day
```

The `--demo` flag exists because EchoSelf's deepest features — personality drift, the Mirror
Report, the Dark Days Protocol — emerge over weeks of real use. Demo mode lets you feel the
lived-in version immediately.

## Project Structure

```
echoself/
├── main.py                  # Entry point
├── core/                    # EchoBuilder, narrative engine, session manager, demo mode
├── character/               # Procedural character renderer, expressions, personality drift
├── learning/                # CodePath lessons, quizzes, challenge runner, progress
├── ml/                      # Behavioral model, psychology layer, synthetic archetypes
├── visual/                  # The three worlds, transitions, analytics charts
├── audio/                   # Procedural soundscape (numpy-synthesized, no audio files)
├── characters/              # Personality packs (JSON, CC BY 4.0)
├── lessons/                 # Lesson packs per language track (JSON, CC BY 4.0)
├── arcs/                    # Narrative arc packs (JSON, CC BY 4.0)
├── exchange/                # Echo Exchange community sentences (CC BY 4.0)
└── data/                    # Your local data — never leaves your machine, never committed
```

## Privacy

EchoSelf is **local-first**. Your profile, logs, letters, and Vault never leave your machine.
There is no server, no telemetry, no account. See [SECURITY.md](SECURITY.md).

## Contributing

Contributions are welcome — both code and creative content (personality packs, lesson packs,
narrative arcs, Echo Exchange sentences). See [CONTRIBUTING.md](CONTRIBUTING.md) for formats and
workflow, and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community guidelines.

## Licensing

EchoSelf uses a **dual-license model**:

- **MIT** — the Python engine (everything in `core/`, `character/`, `learning/`, `ml/`,
  `visual/`, `audio/`, `main.py`). See [LICENSE](LICENSE).
- **CC BY 4.0** — community-contributed creative content (`characters/`, `lessons/`, `arcs/`,
  `exchange/`). See [LICENSE-CONTENT](LICENSE-CONTENT).

Code and creative content have different legal needs; separating them is a deliberate
architectural decision. Third-party dependencies are credited in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Roadmap

- **v1.0** — Character system (custom + 5 prebuilts), ML brain (5-state classification),
  psychology layer with personality drift, full Python CodePath track, three worlds, four-axis
  Echo Distance, Dark Days Protocol, Mirror Report, Vault, Letters, Echo Exchange, procedural
  soundscape, demo + time-lapse modes.
- **v1.5** — C and Java tracks, deeper NLP analysis, cross-session pattern memory.
- **v2.0** — All four language tracks, community lesson pack ecosystem, anonymous peer challenge
  showcase, Echo Circle study pods.

## Why

This project was built from a real feeling — the exhaustion of surviving instead of living, and
the quiet wish for something that knows you without needing you to explain yourself.

EchoSelf does not optimize productivity. It does not gamify discipline. It builds a character that
learns you, teaches you through that character, and slowly, quietly, without announcing it — the
character becomes who you needed them to be all along.

That is also what open source is: something built by people for people, freely given, honestly
maintained, always there.

---

*Created by Prodipta Acharjee — Sejong University, Seoul.*
*Built for "Introduction to Open Source Software" (Prof. Junaid Rashid, Ph.D.) and for anyone who needs it.*
