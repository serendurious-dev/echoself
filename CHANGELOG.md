# Changelog

How EchoSelf grew, layer by layer. It is built so the history itself shows the
work - every feature came in on its own branch and merge.

## v0.3 - senses, depth, and more to learn (current)

She got eyes, a voice, a sharper read of you, more to teach, and a deeper way of
listening. The core still runs offline by default; everything new is opt-in, and
nearly all of it runs on your own machine.

- **A core you can build on** - the brain was pulled out from behind the screen
  (`echoself_core`), so the same companion can drive a phone or the web later, not
  just this window.
- **The warm voice** - with your own key, the conversation and ask-anything
  research can be written by a model in your better-self voice; offline stays the
  default and the safety net, and crisis never reaches it.
- **A sharper read** - an optional local transformer reads tone and context past
  the word list, while the lexicon keeps the finer feelings it names; free,
  offline, your switch.
- **The mirror** (`i`) - an opt-in webcam affect-mirror: she gently reflects your
  expression so you feel seen. On-device, frames never stored, and you can teach
  it your own face so it imitates you.
- **Her voice and ears** - optional local text-to-speech (Piper) and
  speech-to-text (Vosk): she speaks her replies, and `F2` lets you talk to her.
  All on your machine; audio never leaves it.
- **Deeper psychology** - DBT, CBT, and ACT skills now (the right one by how
  intense it is), a normalizing word on what a feeling is doing, a gentle notice
  when one keeps recurring, and a motivational-interviewing stance for when you're
  stuck. A concern tier between comfort and crisis, for the quiet sinking.
- **She follows the conversation** - notices when your feeling shifts mid-talk,
  and remembers when a heavy one comes back around.
- **Six courses now** - Python, C, C++ and Java (each two or three clusters), plus
  a full Data Structures & Algorithms course and a How Computers Work / OS course.
  Switch with `g`, then `1`-`6`.
- **Settings that settle things** (`s`) - toggles for the sharper read, the
  region your crisis lines point to, the mirror, and her voice. A safety plan
  (`k`) you write for the hard moments.
- No more black screen on launch (she shows up while the brain wakes), and
  over 350 tests.

## v0.2 - the companion

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
  she calls you by name. Friend when you're hurting, gentle teacher when you're dodging.
- **Offline by default** - the whole core runs with no network. One optional,
  off-by-default layer (your own key) adds the mirror-self voice and ask-anything
  research, grounded so it refuses rather than guess.
- Richer personality drift (five axes now, including humor), and 244 tests.

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
