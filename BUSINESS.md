# How EchoSelf could sustain itself

EchoSelf is free and open source, and the engine always will be. But "open source" and "has no
way to keep the lights on" are not the same thing, and the course covered the business models
that let open projects survive. This is the one EchoSelf is built for, and why.

## The model: Open Core

EchoSelf uses an **Open Core** model. The core - the whole engine, every feature in this
repository - is free and MIT-licensed forever. Around that core, there's room for optional paid
layers that never close off the free one.

The shape of it:

| Layer | What it is | Cost |
|---|---|---|
| **Free & open** | The engine, the default character art, the Python track, the five personalities, the Vault, everything in this repo | Free, MIT + CC BY 4.0, forever |
| **Community content** | Personality packs, lesson packs, language tracks, narrative arcs - contributed by anyone | Free; contributors may choose to sell their own packs |
| **Hosted sync (possible future)** | An optional account that syncs your local data across devices - same engine, just a backup-and-sync convenience | Subscription, optional, never required |

The line is deliberate: **nothing that makes EchoSelf *work* is ever behind a paywall.** You can
clone this repo, run it forever, and never pay anyone. The only things that could cost money are
*conveniences* (cross-device sync) and *other people's creative work* (premium content packs),
and even those are optional on top of a complete free product.

## Why this model and not another

The course covered several models - support/services, dual licensing, donations, SaaS, Open Core,
and others. Open Core fits EchoSelf because:

- **The dual license already draws the line.** The engine is MIT; the content is CC BY 4.0. That
  same split is the natural seam for Open Core: the code stays free, and a content ecosystem can
  grow on top with its own economics.
- **It respects the philosophy.** EchoSelf's whole stance is presence over pressure - it would
  betray that to lock a struggling person out of the thing that helps them until they pay. Open
  Core lets the helpful part stay free by design, not by charity.
- **It's honest about local-first.** EchoSelf has no server and no telemetry (see SECURITY.md),
  so there's nothing to monetize through data, ever. The only hosted thing that could exist is
  opt-in sync, and that's a service you'd be choosing to buy, not a tax on using the app.

## Who pays, in practice

- **Most people: nobody.** The free engine is the whole experience.
- **Contributors who want to:** an author who writes a beautiful premium personality pack or a
  full language track can sell it. The CC BY 4.0 content license allows commercial use; the
  marketplace is theirs.
- **People who want sync across devices:** a small optional subscription for a hosted backup, if
  that layer is ever built. The engine stays MIT either way.

That's the model: free where it matters, optional where it doesn't, and never a paywall between a
person and the version of themselves they're trying to reach.
