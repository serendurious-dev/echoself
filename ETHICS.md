# Safety and ethics

EchoSelf reads how you feel and tries to be there for you. That is a tender thing
to build, so I want to be plain about what it does, what it refuses to do, and
where its edges are.

## It is a companion, not a clinician

EchoSelf is not therapy, and it is not a therapist. It does not diagnose, it does
not treat, and it does not give medical or clinical advice. It is a caring
presence that draws on a few well-known, everyday coping ideas. If you are
struggling with your mental health, please talk to a real professional - EchoSelf
is meant to sit beside that, never to replace it.

## Crisis comes first, always

If what you write sounds like you might be in danger - thoughts of suicide or
self-harm - EchoSelf drops everything else. It does not try to counsel you, it
does not soften it, and that message never reaches any of the normal response
logic - and never the optional model layer either, even when that layer is turned
on. It does one thing: it stays with you for a moment, tells you honestly that it
is a program and cannot keep you safe, and points you to real human help.

In South Korea: **109** (suicide prevention) or **1393**. Anywhere, in immediate
danger: your local emergency number. The detection deliberately errs toward
catching too much rather than too little - a false alarm costs nothing, a missed
one costs everything.

## How it reads emotion, and what it never keeps

EchoSelf infers your feeling from the words you choose, with a plain offline word
list - no cloud, no model required, nothing sent anywhere. It is a rough read of
the drift of a message, not a verdict on you.

What it stores is only the *signal* - the inferred emotion and how strong it was -
never the words you typed. Your sentences live only for the length of the
conversation and are then gone. The longer-term "portrait" it keeps holds short,
plain facts (never transcripts), and you can open it on the `p` screen, read every
line, and delete any of it. `--forget` erases all of it. See
[SECURITY.md](SECURITY.md) for the full privacy model.

## Support is offered, never forced

When a feeling has a coping tool that fits, EchoSelf offers it - as a question,
once, and only after it has listened first. If you say yes, it walks through it
with you. If you say anything else, it lets it go without a word. You are never
pushed into a technique, and the tools are gentle, ordinary self-help, not
treatment.

## The frameworks it draws on

The coping tools are encoded in `psychology/frameworks.py`, each with its source:

- **5-4-3-2-1 grounding** - for panic. University of Rochester Medical Center,
  Behavioral Health Partners (2018).
- **Paced / diaphragmatic breathing** - for acute stress; common to CBT and DBT.
- **Self-compassion** - for shame. Neff, K. (2003), *Self and Identity* 2(2),
  85-101 (self-kindness, common humanity, mindfulness).
- **Gentle cognitive reframing** - for catastrophising, all-or-nothing, and
  mind-reading. Cognitive behavioural therapy (Beck).
- **One small step (Kaizen)** - for overwhelm and freeze.
- **The dichotomy of control (Stoic)** - for anxiety about the uncontrollable.
  Epictetus, *Enchiridion*.

These are summaries of public, widely taught ideas, adapted into a companion's
voice. They are not a substitute for care from a person who is trained to give it.

## The optional model layer

By default EchoSelf is fully offline and the offline library writes everything she
says. There is one opt-in layer: if you install it and add your *own* API key, a
model can write her replies in a richer "mirror-self" voice. Being honest about
it: when that layer is on, your messages in a conversation are sent to the
Anthropic API to generate the reply. It is off unless you turn it on, it is never
used for a crisis message, and the offline companion remains the default and the
fallback. If privacy is what you want, simply don't enable it - nothing changes
about the rest of the program.

## My promise

I built this to lower pressure, never to add it. If anything here ever makes
someone feel worse, watched, or judged, that is a bug, and it matters more than
any feature. Tell me and I will fix it.
