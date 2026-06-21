# Building the desktop app

EchoSelf runs from source with `python main.py`. To hand someone a standalone app
they can double-click - no Python, no install - bundle it with PyInstaller.

## Build it

```
pip install -r requirements-build.txt
pyinstaller echoself.spec
```

The result lands in `dist/EchoSelf/`. Ship that whole folder; the app is
`dist/EchoSelf/EchoSelf` (or `EchoSelf.exe` on Windows).

## Where things go when packaged

- **The app and its content** (lessons, character art, exchange, arcs) live inside
  the bundle, read-only.
- **Your own data** (profile, logs, the vault, the portrait, settings, the safety
  plan, a calibrated mirror) is written to a real, persistent home so it survives
  between runs - `%APPDATA%\EchoSelf` on Windows, `~/.local/share/EchoSelf`
  otherwise. `core/paths.py` is the single place that decides this.

## What's left out, on purpose

The build is the **offline** app. The opt-in layers - the API-key voice and
research, the local emotion transformer, the webcam mirror, the spoken voice - are
deliberately excluded so the build stays small (those deps are large). A user who
wants them installs the matching `requirements-*.txt` and runs from source.

## Notes and likely tweaks

- The window has no console. To see errors while debugging a build, set
  `console=True` in `echoself.spec` and rebuild.
- scikit-learn is named in the spec's `hiddenimports` because the brain imports it
  lazily. If a build still can't find it, add `--collect-all sklearn` (and the same
  for `scipy`) to the PyInstaller call.
- The editor-handoff coding challenges run the user's solution with a Python
  interpreter, so they only work when running from source, not in the packaged app.
- This spec is verified to be correct in structure; run the build on the target OS
  and confirm the app launches there.
