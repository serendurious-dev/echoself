# Security

## The privacy model

EchoSelf is local-first, and that is not a feature, it is the foundation. A person cannot
write honestly into something they do not trust.

- No server, no account, no telemetry. Nothing leaves your machine.
- Everything you generate lives in the local `data/` directory: your profile, the session
  and learning logs, the model file, your letters, the Vault.
- `data/` is gitignored, so your data cannot be committed or pushed even by accident.
- **The Vault is never read.** It is encrypted at rest and no part of the system parses,
  analyzes or trains on its contents. The system holds it. It does not look at it.
- The ML model trains on interaction metadata only — timing, session length, quiz accuracy.
  Never on the text of anything you wrote privately.

## Supported versions

| Version | Supported |
|---|---|
| `main` | yes |
| anything older | no, please update |

## Reporting a vulnerability

If you find something — especially anything that could expose local data, weaken the Vault,
or make EchoSelf transmit anything — please tell me privately first:

1. Preferred: GitHub Security Advisories on this repo ("Security" tab → "Report a
   vulnerability").
2. Or email `prodiptaach0109@gmail.com` with the subject `[EchoSelf Security]`.

Include how to reproduce it. Please do not open a public issue for a security problem
before there is a fix. I will acknowledge within 72 hours, and reporters get credited in
the release notes if they want to be.

## A note for contributors

Pull requests that add network calls, analytics, or any read access to the Vault get
rejected on sight, whatever the intent. It is in [CONTRIBUTING.md](CONTRIBUTING.md) too,
but it belongs here as well.
