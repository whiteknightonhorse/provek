# FILM_SCRIPT — the three landing-page clips

Committed verbatim from Fable's brief (2026-08-31), unedited. This is the source of truth D-42's
predicate 1 checks burned-in text against, character-for-character: acceptance gates compare the
title cards on the raw render to this document, not to memory or to chat history. Do not edit this
file to match a render — if a render disagrees with this script, the render is wrong (D-28's
forward-only discipline: fix the render, not the record it is judged against).

Placement, admissibility and enforcement live in `DECISIONS.md` D-42, not here. This file is the
shot list and dialogue only.

## Characters

**SHOPBOT** — a squat, counter-height shopkeeper robot. Worn cream-and-brass casing, one large
round amber eye-lens. Its lines render in amber (`--c-warn #d9a85c`).

**COURIERBOT** — a narrow, hovering courier robot. Matte graphite casing, a thin pale-blue visor.
Its lines render in blue (`--c-accent #82b0e0`).

Eye colour = dialogue colour = the page's own colour token, for both characters.

## Structure

One story across three acts, each closed on its own beat — a viewer may land on the slider at any
of the three. Clip = 4 s. One video = 3 clips = 12 s. Video 3 gets +3 s of a static title card.
Full cycle = 39 s.

## Video 1 — "THE ORDER"

- **1.1** Wide shot, a booth-office. SHOPBOT behind the counter, COURIERBOT hovering, a blue
  hologram between them. On-screen text: `ORDER — $5,000` → `> ORDER ACCEPTED`
- **1.2** Close on a graphite hand reaching for an amber hexagonal button; it freezes. Overlay
  `PAY`. A pause. Below, in blue: `PASSPORT?`
- **1.3** Close on SHOPBOT, its amber eye widening. In amber: `WHAT?` → in blue:
  `AI BUSINESS PASSPORT.`

## Video 2 — "THE PROOF"

- **2.1** Medium shot across the counter, the hologram dimmed. In amber: `I'M AUTONOMOUS.` → in
  blue: `YEAH. PROVE IT.`
- **2.2** SHOPBOT projects a wall of flickering star-glyphs from its chest. In amber:
  `I HAVE A GITHUB.` → in blue: `THAT'S NOT A PASSPORT.`
- **2.3** The hologram half-frame, SHOPBOT gesturing proudly, COURIERBOT motionless, a slow push-in
  on its empty visor. In amber: `LOOK. 4,000 STARS.` → in blue, larger: `PASSPORT.`

## Video 3 — "THE PASSPORT"

- **3.1** Overhead close shot: a brass hand slides a card across the counter, glowing blue at the
  edge, with a round seal. Overlay `AI BUSINESS PASSPORT`, no dialogue.
- **3.2** The visor sweeps a scanning beam across the card; a green glow rises from the seal.
  `> CHECKING EVIDENCE…` → in green (`#6fb37c`) `VERIFIED` with small text below it
  `(NOT FOREVER)`
- **3.3** Wide shot as in 1.1, the hologram calm and green, the hand presses the button. In green,
  cascading: `PAY ✓  EXECUTE ✓  COMPLETE ✓`
- **3.4** Title card, 3 s static, background `#191b20`:
  `AI agents will do business with AI agents.` / `They need a way to prove who they are.` →
  `PROVEK` / `provek.dev`

## Timing within a clip

Line 1: 0.4–2.0 s. Line 2: 2.2–3.9 s. Appearance: 100 ms fade-in. Captions are monospace,
UPPERCASE, burned in by `ffmpeg drawtext`.

## No VERIFIED UI in any frame

Fable ruled this separately and it is recorded here so step 6's executor cannot lose it: **no frame
contains a user-interface element that reads `VERIFIED`.** The operator's original draft ended on a
`VERIFIED → PAY → EXECUTE` screen — exactly the image-of-a-measurement D-42 keeps forbidden
(predicate 2: no interface, document, chart, data screen, or number in frame). In 3.2, `VERIFIED`
is a burned-in post-title caption sitting over a fictional card prop — the same `ffmpeg drawtext`
layer every other caption in this script uses — never a rendered interface panel in the shot itself.
The distinction is load-bearing: a caption is text about the scene; a UI reading `VERIFIED` would be
the scene presenting itself as an instrument, which is the one thing predicate 2 exists to keep out.

## Substitution blocks

`[STYLE]`:
> Still from a 1990s retro-futuristic science fiction film. Cramped, cluttered future-city interior
> at night. Deep charcoal-blue shadows, warm amber practical lamps, pale ice-blue holographic
> light. Light haze, 35mm film grain, shallow depth of field, anamorphic cinematic framing, 16:9.
> No humans. No readable text, letters, numbers, or logos anywhere in frame.

`[SHOPBOT]` = a stocky counter-service robot with a scuffed cream-and-brass sheet-metal chassis,
one large round amber optic lens, short thick arms, standing behind a cluttered metal counter

`[COURIERBOT]` = a slim hovering courier robot with a matte graphite shell, a narrow pale-blue
optic visor, thin articulated arms

## Frames K1–K9 (Replicate, GPT Image 2)

- **K1**: `[STYLE] Wide shot: [SHOPBOT] facing [COURIERBOT] hovering in front of the counter. Between them a translucent pale-blue holographic panel glows above the counter, showing only abstract glyph-like shapes. Cables, crates and unmarked old signage crowd the background.`
- **K2**: `[STYLE] Close shot over the counter: the slim graphite arm of [COURIERBOT] reaching toward a large glowing amber hexagonal button mounted on the counter, fingertip a few centimeters away, frozen mid-air. The amber light reflects on the graphite hand. Background heavily blurred.`
- **K3**: `[STYLE] Medium close-up of [SHOPBOT]: its single large amber optic lens wide open, head unit tilted slightly, tiny status lights blinking on its chest. Shelves of unmarked boxes behind.`
- **K4**: `[STYLE] Medium two-shot: [SHOPBOT] and [COURIERBOT] facing each other across the counter, the holographic panel dimmed, tense stillness, haze drifting through the amber lamplight.`
- **K5**: `[STYLE] [SHOPBOT] projects from its chest a large translucent pale-blue hologram filled with rows of small glowing star-shaped glyphs, like a wall of tiny stars. [COURIERBOT] hovers motionless, its visor reflecting the hologram, unimpressed posture.`
- **K6**: `[STYLE] The star-glyph hologram now fills half the frame, sparkling; [SHOPBOT] gestures at it proudly with both short arms; [COURIERBOT] perfectly still in the foreground, seen from behind its shoulder.`
- **K7**: `[STYLE] Top-down close shot of a scratched metal counter: [SHOPBOT]'s brass hand sliding forward a slim rectangular card-like device glowing soft pale blue along its edges, with an embossed blank circular seal. Amber lamp reflections on the metal.`
- **K8**: `[STYLE] Close shot: [COURIERBOT]'s visor emitting a thin pale-blue scanning beam sweeping across the glowing card held in its thin hand; a faint green light beginning to rise from the card's seal.`
- **K9**: `[STYLE] Wide shot, same framing as K1: both robots at the counter, the holographic panel above now glowing calm green, [COURIERBOT]'s arm pressing the amber hexagonal button, relaxed postures.`

**Before K1–K9**, two character reference sheets are generated, one per robot:

> `character reference sheet, three views, neutral grey background, [SHOPBOT or COURIERBOT], lighting from [STYLE]`

(Fable's own line used two Russian connector words at this point - a conjunction and a short
phrase meaning "lighting from" - which this file renders as "or" and "lighting from" so the
actual prompt text is valid English throughout, per this repository's English-only rule; the
placeholders and structure are otherwise unchanged.)

Each K-prompt then runs WITH THIS REFERENCE — continuity across the nine clips cannot hold without
it.

## Motion M1–M9 (Renoise, Seedance 2.0, image-to-video, 4 s)

- **M1**: `Subtle cinematic motion: the hologram flickers gently, dust drifts in the amber light, the counter robot nods slowly once, the courier robot hovers with a slight bob. Static camera with a very slow push-in.`
- **M2**: `The arm moves slowly toward the glowing amber button, then stops abruptly mid-air and holds still. The button keeps pulsing softly. Static camera.`
- **M3**: `The amber optic lens irises wider, the head unit tilts, chest status lights blink. Slow push-in. No other motion.`
- **M4**: `Both robots hold perfectly still facing each other; the hologram flickers dimly; haze drifts. Very slow lateral dolly.`
- **M5**: `The star hologram unfolds upward from the robot's chest, star glyphs twinkling; the courier robot stays motionless. Static camera.`
- **M6**: `The hologram sparkles brighter, the counter robot gestures at it with both arms; the courier robot remains perfectly still. Slow push-in on the courier robot's blank visor.`
- **M7**: `The brass hand slides the glowing card slowly across the counter toward camera, its edge-glow pulsing once. Static top-down camera.`
- **M8**: `A thin scanning beam sweeps across the card twice, left to right; green glow rises from the seal and softly fills the lower frame. Static camera.`
- **M9**: `The arm presses the amber button; the overhead hologram turns green and pulses three times; both robots give each other a single nod. Slow pull-back.`

## Frame-to-clip correspondence

1.1→K1/M1 · 1.2→K2/M2 · 1.3→K3/M3 · 2.1→K4/M4 · 2.2→K5/M5 · 2.3→K6/M6 · 3.1→K7/M7 · 3.2→K8/M8 ·
3.3→K9/M9 · 3.4 — static title card, needs no generation.

## Palette

- `--c-paper #191b20` — shadow base and the title card's background
- `--c-ink #e8e6e1` — title card text
- `--c-accent #82b0e0` — the hologram, the visor, COURIERBOT's lines
- `--c-warn #d9a85c` — the lamps, the button, SHOPBOT's eye and lines
- `--c-pass #6fb37c` — the VERIFIED moment ONLY, once across all three videos

## Forbidden in frame

- Any recognisable image from the film this is inspired by (checked coats, bandages, the suits, the
  word "Multipass")
- Zero readable generated characters
- No company name on the passport card
- PROVEK never appears next to payment UI
- No registry numbers
- No user-interface element reading `VERIFIED` (or anything else) visible in any shot — see
  "No VERIFIED UI in any frame" above; 3.2's `VERIFIED` is a burned-in caption, never an on-screen
  interface
