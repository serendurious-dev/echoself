# Art packs

A character can be drawn two ways. The default is procedural - the figure in
`character/renderer.py`, drawn entirely by code, no image files. The other way is
an **art pack**: layered PNGs composited and animated like a visual-novel app, so painted
art can be the body instead. This folder is where art packs live.

The engine picks automatically: if a character's `visual.art` names a pack folder here that
has a `manifest.json`, you get the layered art; otherwise it falls back to the procedural
figure. A broken pack falls back too - the app never refuses to start.

## Folder layout

```
characters/art/<pack-id>/
|-- manifest.json
|-- back_hair.png
|-- body.png
|-- head.png
|-- eyes_open.png
|-- eyes_closed.png
|-- mouth_neutral.png
|-- mouth_happy.png
|-- mouth_open.png
`-- front_hair.png
```

All layer images are the **same size** (one frame) with a transparent background, so they
overlay in place. The character's height scales the whole frame; `feet` says where the
ground is.

## manifest.json

```json
{
  "name": "Aria",
  "feet": [0.5, 0.99],
  "layers": [
    {"image": "back_hair.png",   "z": 0, "motion": "hair"},
    {"image": "body.png",        "z": 1, "motion": "body"},
    {"image": "head.png",        "z": 2, "motion": "head"},
    {"image": "eyes_open.png",   "z": 3, "motion": "head", "eyes": "open"},
    {"image": "eyes_closed.png", "z": 3, "motion": "head", "eyes": "closed"},
    {"image": "mouth_neutral.png","z": 4, "motion": "head", "mouth": "neutral"},
    {"image": "mouth_happy.png", "z": 4, "motion": "head", "mouth": "happy"},
    {"image": "mouth_open.png",  "z": 4, "motion": "head", "mouth": "open"},
    {"image": "front_hair.png",  "z": 5, "motion": "head"}
  ]
}
```

- `z` - draw order, low to high.
- `motion` - how the layer breathes: `body` (rises with the breath), `head` (lags half a
  beat), `hair` (follows the head, a touch more swing), or `none`.
- `eyes` - tag the open and closed eye layers; the engine swaps them to blink.
- `mouth` - tag mouth layers `neutral` / `happy` / `open`; the engine picks one per
  expression (happy and patient -> happy, celebrating -> open, the rest -> neutral).
- `expr` - optional list of expression names; the layer only shows for those (e.g. a blush).

Then point the character at it:

```json
"visual": { "art": "aria", ... }
```

## Using a clean open-licensed pack

The point of this system is that you can drop in real art with a license you can defend in a
paper. Good sources of **CC0** layered visual-novel sprites with expression sets:

- itch.io, filtered to free visual-novel sprite assets (Exuin's and DoubleFree's packs are CC0).
- OpenGameArt.org CC0 character art.

Slice or rename the pack's layers to match the manifest above, drop the folder here, set
`visual.art`, and it renders. **Record the source and license** of any pack you add in its
folder (a `LICENSE.txt` next to the images) - that is the whole reason to use clean art.

## Placeholder

`python tools/make_placeholder_art.py` writes a plain placeholder pack to `_placeholder/`
so you can watch the pipeline work (layers, blink, mouth, breathing) before real art exists.
It is deliberately ugly. It is not committed.
