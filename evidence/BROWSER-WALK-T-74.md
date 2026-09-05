# BROWSER-WALK-T-74 — operator's live-site verification, transcribed

tree: fd551adab5a16fd941a49081abfbac45668f5598

Source: dispatcher's two reports on T-74's active task file (`~/taskloop/active/74-ai-agent-templates-phase4-final-walk.md`),
2026-09-05 ~05:0x UTC and ~05:2x UTC, run from the operator's laptop via `claude-in-chrome`
against the live `provek.dev` at deploy label `bc5a296`. Direct write access to
`~/taskloop/disputes/74-....operator-1.md` was permission-denied for the dispatcher, the same
failure mode as `ruling-1.md` — so this file is the transcription the ruling (§4.1) asked the
executor to produce from the inline report, not a copy of an on-disk `operator-1.md`.

Screenshots referenced below live on the operator's laptop only (per the ruling's protocol, §3);
this file records their filenames and the measurements taken alongside them, not the images.

## P1 — viewport / horizontal overflow — PASS, 9/9

Pages: `/build/`, `/build/customer-support-agent/`, `/build/finance-operations-agent/`.
Widths: 360 / 768 / 1440. All 9 combinations: `horizontalScroll: false`, offenders list empty.
Measured document widths: 360 → 349, 768 → 757, 1440 → 1429.

Method note: the Chrome window itself would not size below 768, so 360 was measured inside a
360px-wide nested frame — the document inside sees a real 360 viewport and media queries respond
to it accordingly.

Control: a planted 1200px-wide block in the same frame produced `horizontalScroll: true` at a 360
viewport; removing the plant returned the document to 349. The zero above came from a check that
is shown able to go red.

## P2 — console errors — PASS, 0 real errors across 9 loads

One message appeared across all nine page loads: the operator's own planted
`console.error('CONTROL-PLANT')`. Zero unplanted errors. The plant demonstrates the check would
have caught a real one.

## P3 — Copy, real click + real system clipboard — PASS, 3 real clicks, 3 byte-identical results

Real pointer clicks on the rendered Copy button, followed by a real system-clipboard paste
(`cmd+v` into a scratch textarea, not `navigator.clipboard.readText()` and not an intercepted
handler), hashed client-side before any paste-induced newline translation could occur:

| source | tool selected | clipboard length | source file length | sha256[:16] | verdict |
|---|---|---|---|---|---|
| `/build/customer-support-agent/` page, layer-1 Copy | Cursor | 10754 B | 10754 B | `072dd28c74e6aeaf` | byte-identical |
| `/build/finance-operations-agent/` page, layer-1 Copy | Claude Code | 10155 B | 10155 B | `66b0386334819fba` | byte-identical |
| `/build/` index card, Lead Generation | (index card, no tool selector) | 9506 B | 9506 B | `e9625d0a64a7dbbe` | byte-identical |

Control: the three hashes are pairwise distinct and each matches only its own source file — the
check discriminates between templates rather than passing on any non-empty clipboard. For the
index-card click specifically: button states read `Copy ×6` before the click and
`Copy, Copied, Copy, Copy, Copy, Copy` immediately after — the clicked card's button, and only
that one, changed state, confirming the click landed on the intended (second) card and not a
neighbour.

This exercises the same three channels `tests/test_template_copy_is_the_artefact.py` now arms
mechanically (commit `d289f09`): a template page's `<pre>`/raw-sibling pair, and the `/build/`
index card's `window.__PROVEK__.templates[].raw` read path. The two Copy tools not sampled here
(Codex, Other) remain covered only by the unit-level DOM-read test, not by an operator click.

## P4 — nav / spacing / type parity — PASS

`/build/`, `/registry/`, `/method/` compared at 1440: nav text identical character-for-character
(`Registry Method Build Corpus, not available`), font `IBM Plex Sans`, base size 16px, background
`rgb(18,19,23)`, foreground `rgb(232,230,225)`, `h1` 28px — all four tokens match across all three
pages.

## P5 — dark theme — PARTIAL, boundary named

Rendered result inspected: dark palette matches the existing pages on the tokens measured in P4;
no new colors observed by eye.

**NOT MEASURED:** no in-page theme toggle exists, and `prefers-color-scheme` could not be
overridden with the tools available to the operator in this session. The light theme was **not
verified** at all. This is recorded as not-measured, not as passing — a separate pass (e.g. via
browser devtools media-feature emulation, not attempted here) would be needed to close it.

## P6 — §24, first-time-reader verdict — NOT OBTAINED

The ruling (§3, P6) assigns this verdict to the operator personally, first thing, before
consulting the brief: one sentence on what the page is and what to do on it, plus
understood/not-understood. The operator was asked directly. As of this transcription, **no
response has been recorded**. This is the one row of the final-walk table this file cannot close.

## Disposition for the final-walk table

Rows 1, 8, 9, 17, 19 (browser-dependent parts) close against P1–P4 above, **except** the
dark/light-theme portion of 9/16/19, which stays NOT MEASURED (light theme) rather than DONE.
Row 24 stays open pending an operator verdict — it is not this file's, or the executor's, to
supply.
