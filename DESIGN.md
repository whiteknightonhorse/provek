# Design

<!-- impeccable:design-schema 1 -->

Derived from the shipped build at the end of phase 4, not from intentions. Every value below is in
`web/src/index.css` or a component; where the two ever disagree, the code is right and this file is
stale.

## The world

A public record, not a product page. The reference points were Certificate Transparency, the NVD,
and SSL Labs: surfaces where a reader arrives under obligation, reads one document once, and needs
to know what the issuer did *not* establish as much as what it did.

Two commitments follow, and they explain most of the choices:

1. **Absence is the identity.** The one visual device is the unfilled slot. It exists because the
   product's argument is that undistinguished absence is the defect worth paying to detect, and a
   surface that renders absence as a dash or a blank would be making that defect its house style.
2. **Nothing may make an unmeasured fact quieter than a measured one.** No lighter ink, no smaller
   type, no neutral grey. This rules out the obvious typographic move and is the reason
   `--color-unknown` sits at the same contrast floor as secondary text.

## Type

| role | face | where |
|---|---|---|
| body, headings | IBM Plex Sans (400 / 500 / 600) | everything that is prose |
| machine values | IBM Plex Mono (400) | identifiers, levels, dates, versions, reasons |

IBM Plex because it was drawn for technical documents, and because its mono is a sibling of its
sans rather than a stranger — a subject id sits in a sentence without looking pasted in. Both are
self-hosted through `@fontsource`; the page makes no external font request.

Scale, from `@theme`, roughly 1.25 with tracking that tightens as size grows:

```
xs   0.75rem   / 1.5   / +0.01em
sm   0.875rem  / 1.6   / +0.002em
base 1rem      / 1.65
lg   1.125rem  / 1.45  / -0.008em
xl   1.375rem  / 1.3   / -0.014em
2xl  1.75rem   / 1.22  / -0.02em
3xl  2.25rem   / 1.15  / -0.026em
5xl  3.25rem   / 1.02  / -0.03em
```

Reading measure is set in `ch`, not `rem`, so it stays tied to the face actually in use: 70ch for
document prose, 62ch for the landing. Numbers are `tabular-nums` in every table, list and time
element — two eighty-somethings must be the same width down a column.

## Colour

Two authored palettes, not one palette and its inversion. Runtime values live on `:root` as
`--c-*`; `@theme inline` maps them onto Tailwind's `--color-*` names, so a component references a
token and never a literal. There are **zero** hex values in any component.

Light is a warm paper (`#fffefb` on a `#f5f3ee` ground) because a pure-white document glares under
a desk lamp. Dark is slate (`#191b20` on `#121317`) with ink stopping at `#e8e6e1` — never pure
white, which vibrates on a dark ground.

| token | light | dark | note |
|---|---|---|---|
| `ink` | `#16171c` | `#e8e6e1` | |
| `ink-2` | `#464b57` | `#b2b0aa` | secondary prose |
| `ink-3` | `#666c78` | `#8f8d88` | metadata |
| `unknown` | `#666c78` | `#8f8d88` | **identical to `ink-3` on purpose** |
| `accent` | `#1b4b7a` | `#82b0e0` | links only |
| `pass` / `warn` / `fail` | `#2c6b3c` / `#8a5b12` / `#9b2b2b` | `#6fb37c` / `#d9a85c` / `#e08a8a` | ladder levels |
| `slot` | `#8d8677` | `#6a707a` | 3.58 / 3.46 — the non-text floor is 3 |
| `ink-disabled` | `#8e8a83` | `#6a6e78` | reserved phase-2 slots |

Theme resolution covers all three viewer states: bare `:root` carries the complete light palette,
`@media (prefers-color-scheme: dark)` is guarded as `:root:not([data-theme="light"])`, and the
`[data-theme]` stamps win in both directions. No colour is defined only inside a media query.

## The device

```css
.slot {
  display: inline-block;
  min-width: 2.75ch;
  height: 1em;
  border-bottom: 2px solid var(--c-slot);
  vertical-align: baseline;
}
```

A ruled blank on the line the value would have occupied. It replaces the question mark everywhere
absence appears: the level rail, every accountability row, an absent projection. Two rules govern
it:

- **A slot is never accompanied by a solid mark.** The colour bar under a level rail is suppressed
  when the level is unmeasured — a filled bar under a blank contradicts the blank.
- **A slot always carries its reason in the accessible name**, never in a `title`. A reason
  reachable only by a mouse has not been published.

## Components

- **Strip** — a finding callout. Tone is a wash plus a 1px rule, never a coloured bar down the
  side; the bar is the category's default for "callout" and carries nothing the tint does not.
- **Facts** — a two-column definition list. Label above value below 640px, side by side above.
  Sub-detail goes inside the cell; there are no nested cards anywhere in this design.
- **LevelRail** — the level, and a colour bar only when measured.
- **stack-table** — below 640px the registry's five columns become a stack. No field is dropped;
  the affiliation marker in particular is never hidden by width.

## Motion

Restraint is the brief. The passport is a document: nothing on it moves before the reader asks.
Motion exists to confirm that something happened, and in exactly one place to pace an argument.

- **Durations** 120ms (feedback) and 170ms (arrival), easing `cubic-bezier(0.16, 1, 0.3, 1)` —
  exponential ease-out, which reads as arrival rather than travel. The reveal runs 300ms.
- **Nothing animates a layout property.** Measured: CLS 0 across load and five route changes.
- **Feedback:** colour transitions on links, buttons, rows and inputs; a 1px press.
- **Arrival:** content settles from 0.75 opacity, never from 0. A fade from nothing is a flash of
  missing page, and the skeleton it replaces already occupied the space.
- **Waiting:** skeleton bars breathe on a 1.8s cycle. A shimmer sweep says "look at me"; a slow
  breath says "still going", which is the true message.
- **The one authored moment:** the landing's *limits* list. Each refusal arrives as it is reached.
  It is the only section on the site where order carries information, which is the only reason to
  pace anything.

`prefers-reduced-motion: reduce` is **not** a blanket kill. Travel is what triggers vestibular
symptoms, so travel goes and feedback stays: animations resolve to `none`, the press offset is
dropped, and colour, border, outline and shadow transitions continue. A global `0.01ms` rule would
leave the reader who asked for less motion with less information than everyone else.

The reveal's offset is applied by script and released by script, with a two-second valve. A reader
whose JavaScript never runs, and a reader whose observer never fires, both see the list where it
belongs rather than eight pixels low forever.

## Rules a future change must not break

1. No fact carried by colour alone; no reason reachable only by hover.
2. Contrast measured against **both** grounds, never white alone, and in both themes.
3. Every number on screen exists in the emitted artefact. Nothing is computed for display.
4. Reserved phase-2 surfaces stay disabled and unannounced. Retrofitting a column into a finished
   table is a redesign, not an addition.
5. No emblem or wordmark beyond the name set in type. An emblem earned before a method is the
   substitution this product exists to detect.

## Known open items

Carried from `web/AUDIT.md`: 222 KB of JavaScript serves five static routes. The reduced-motion
rule and the landing's empty right half were both closed in phase 5.
