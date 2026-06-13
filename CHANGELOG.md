# Changelog

How EchoSelf grew, layer by layer. It is built so the history itself shows the
work - every feature came in on its own branch and merge.

## v0.2 - the companion (current)

The learning app became what it was always meant to be: an ambient, fully offline
companion that learns you and stays with you.

- **She holds a real conversation** - multi-turn, opens to your own time of day,
  asks, then deepens instead of repeating. The thread lives only in memory.
- **The portrait** - she remembers you between days: distilled facts, never your
  words, all viewable and deletable on the `p` screen.
- **She reaches out** - a real once-a-day desktop notification (PowerShell toast,
  no dependency), in your waking hours, skipped if you already came by.
- **The daily check-in is a conversation now**, not a one-word form; the mood is
  read from what you say and logged underneath.
- **Psychology, with care** - ten emotions read from text, six sourced coping
  tools offered gently and only on a yes, crisis always first. See `ETHICS.md`.
- **Emotion feeds the brain** - the behavioral model gained a seventh signal: how
  you've been feeling, read from your conversations.
- **Make yourself** - a full from-scratch character builder, and remake (`b`) any
  time. Look and voice are chosen apart.
- **Don't give up** - a mastery dashboard (`g`): per-topic progress, the next
  step, a momentum that never shames a break, a welcome back with no blame.
- **Four languages** - Python deep (with real editor-handoff coding challenges),
  plus C, C++, and Java as quiz-based intro tracks.
- **A way in** - a help screen (`h`, and automatically after Session Zero), and
  she calls you by name.
- **100% offline** - the optional API layer was removed; no external service, no
  network, all the program's own code.
- Richer personality drift (five axes now, including humor), and ~238 tests.

## v0.1 - the learning companion (the course foundation)

- The three worlds (Ambient, Learning, Drift) and one shared sky.
- A code-drawn procedural character + five personality packs, later a painted
  art pack (Codel, CC BY 4.0).
- Session Zero - onboarding that is secretly the ML brain's first calibration.
- The ML brain: a scikit-learn classifier over behavioral signals -> five states.
- The psychology layer and silent personality drift.
- CodePath: the full Python track, quizzes + editor-handoff challenges, a
  three-hint system, and spaced repetition.
- The emotional core: four-axis Echo Distance, Dark Days, Mirror Report, the
  Vault, Letters, Echo Exchange, a numpy soundscape, demo + time-lapse modes.
- The OS layer: a daemon, a file lock, atomic writes, IPC, signals, crash
  recovery, `--doctor`.
- The full OSS suite: dual license (MIT + CC BY 4.0), CI, data export/forget,
  and the docs.
