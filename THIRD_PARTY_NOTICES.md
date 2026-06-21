# Third-Party Notices

EchoSelf stands on these open source projects, and I am grateful to the people who maintain
them. Copyright notices are preserved as each license requires.

| Dependency | Purpose in EchoSelf | License | Project |
|---|---|---|---|
| **Pygame** | Visual engine - the three worlds, the procedural character | LGPL 2.1 | https://www.pygame.org |
| **matplotlib** | Echo Distance radar chart, 30-day timeline | Matplotlib License (PSF/BSD-style) | https://matplotlib.org |
| **NumPy** | Numerical processing, procedural soundscape synthesis | BSD 3-Clause | https://numpy.org |
| **scikit-learn** | ML behavioral model (5-state psychological classification) | BSD 3-Clause | https://scikit-learn.org |
| **pandas** | Session and learning log analysis | BSD 3-Clause | https://pandas.pydata.org |
| **Python standard library** | JSON/CSV storage, encryption primitives (`hashlib`, `secrets`), CLI | PSF License | https://www.python.org |

## License Notes and Obligations

### Pygame - LGPL 2.1
Copyright © Pygame developers.
EchoSelf imports Pygame as an unmodified library dependency, which the LGPL permits without
imposing copyleft on EchoSelf's own code. The library's source is available at its project page.
Full license: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html

### matplotlib - Matplotlib License (BSD-compatible, PSF-based)
Copyright © 2002-2026 John D. Hunter, Michael Droettboom and the Matplotlib development team.
Full license: https://matplotlib.org/stable/project/license.html

### NumPy - BSD 3-Clause
Copyright © 2005-2026 NumPy Developers.
Full license: https://numpy.org/doc/stable/license.html

### scikit-learn - BSD 3-Clause
Copyright © 2007-2026 The scikit-learn developers.
Full license: https://github.com/scikit-learn/scikit-learn/blob/main/COPYING

### pandas - BSD 3-Clause
Copyright © 2008-2026, AQR Capital Management, LLC, Lambda Foundry, Inc. and PyData Development
Team; © 2011-2026, Open source contributors.
Full license: https://github.com/pandas-dev/pandas/blob/main/LICENSE

### Contributor Covenant - CC BY 4.0
Our CODE_OF_CONDUCT.md is adapted from the Contributor Covenant v2.1,
© Coraline Ada Ehmke, licensed CC BY 4.0. https://www.contributor-covenant.org

## Optional dependencies (all off by default)

None of these are installed or used unless you choose to. Three of the four layers
below run **entirely on your machine** - only the mirror-self / research layer uses
the network, and only with your own key.

| Optional layer | Dependency | License | On-device? |
|---|---|---|---|
| Mirror-self voice + research (`requirements-llm.txt`) | anthropic | MIT | no - your API key, over the network |
| Sharper emotion reading (`requirements-nlp.txt`) | transformers | Apache-2.0 | yes |
| | torch (PyTorch) | BSD-3-Clause | yes |
| Webcam affect-mirror (`requirements-vision.txt`) | mediapipe | Apache-2.0 | yes |
| | opencv-python | Apache-2.0 (OpenCV); MIT (packaging) | yes |
| Her voice + ears (`requirements-voice.txt`) | piper-tts | MIT | yes |
| | vosk | Apache-2.0 | yes |
| | sounddevice | MIT | yes |

### anthropic - MIT
The mirror-self conversation + research layer (`requirements-llm.txt`) uses the
`anthropic` Python SDK, © Anthropic, licensed MIT. It activates only when the user
installs it and supplies their own `ANTHROPIC_API_KEY`. When enabled, that layer -
and only that layer - sends data to the Anthropic API over the network. Crisis
messages never reach it.

### transformers - Apache-2.0, torch - BSD-3-Clause
The optional local emotion model (`requirements-nlp.txt`) uses Hugging Face
`transformers` (© Hugging Face, Apache-2.0) over PyTorch (© Meta and contributors,
BSD-3-Clause). The model runs locally; nothing is sent anywhere.

### mediapipe - Apache-2.0, opencv-python - Apache-2.0 / MIT
The optional webcam affect-mirror (`requirements-vision.txt`) uses Google
`mediapipe` (© Google, Apache-2.0) and `opencv-python` (OpenCV © OpenCV team,
Apache-2.0; the Python packaging MIT). Frames are read locally and dropped; no
image ever leaves the machine.

### piper-tts - MIT, vosk - Apache-2.0, sounddevice - MIT
The optional voice (`requirements-voice.txt`) uses `piper-tts` (MIT) for local
neural speech, `vosk` (© Alpha Cephei, Apache-2.0) for local speech-to-text, and
`sounddevice` (© Matthias Geier, MIT) for audio I/O. All of it runs on your
machine; audio is never stored or sent.

## EchoSelf's Own Licenses

- Engine code: MIT - see [LICENSE](LICENSE)
- Creative content (`characters/`, `lessons/`, `arcs/`, `exchange/`): CC BY 4.0 - see
  [LICENSE-CONTENT](LICENSE-CONTENT)

Modifications to this project are tracked in the public git history of this repository,
there is no separate changelog to fall out of date.
