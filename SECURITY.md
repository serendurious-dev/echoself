# Security Policy

## EchoSelf's Privacy Model

EchoSelf is **local-first by design**. This is not a feature; it is the foundation the entire
project stands on.

- **No server. No account. No telemetry.** Nothing you do in EchoSelf leaves your machine.
- All user data lives in the local `data/` directory: `profile.json`, `echo_log.csv`,
  `learning_log.csv`, `user_model.json`, letters, and the Vault.
- `data/` is excluded from version control by `.gitignore` — your data can never be accidentally
  committed or pushed.
- **The Vault** is encrypted at rest using Python standard library primitives. Its contents are
  never read, parsed, analyzed, or used as ML features by any part of the system. The system
  holds it; it does not look at it.
- The ML behavioral model trains only on interaction metadata (response timing, session length,
  quiz accuracy) — never on the text of private writing.

## Supported Versions

| Version | Supported |
|---|---|
| `main` branch | ✅ |
| Tagged releases < latest | ❌ — please update |

## Reporting a Vulnerability

If you discover a vulnerability — especially anything that could expose local user data, weaken
Vault encryption, or cause EchoSelf to transmit data — please report it privately:

1. **Preferred:** open a private report via GitHub Security Advisories
   ("Security" tab → "Report a vulnerability").
2. **Alternative:** email the maintainer at `prodiptaach0109@gmail.com` with subject
   `[EchoSelf Security]`.

Please include reproduction steps and affected files. Do not open a public issue for security
problems before a fix is available.

You can expect an acknowledgment within 72 hours. Once fixed, reporters are credited (with
permission) in the release notes.

## Scope Notes for Contributors

Pull requests that add network calls, analytics, or any read access to Vault contents will be
rejected on security grounds regardless of intent. See CONTRIBUTING.md.
