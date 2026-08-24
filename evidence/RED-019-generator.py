#!/usr/bin/env python3
"""Produces evidence/RED-019-an-offer-narrower-than-what-arrives.txt.

    python3 evidence/RED-019-generator.py            # writes the artefact beside this file
    python3 evidence/RED-019-generator.py --check    # runs everything, writes nothing

WHAT IT ESTABLISHES. That `tests/test_apply_names_the_probe_cost.py` CAN fail (invariant 5), in
each of the directions the gate is filed under - and that it does NOT fail on the rewrites
of the copy that are true. The second half is not decoration. Fable's sharpest finding against the
second draft was a FALSE RED: `three HTTP requests` made the gate say the offer stated no count at
all, over a page that stated exactly the right one. A gate that reds on truthful copy is walked
past just as fast as one that greens on lies (L-5), so the green runs are evidence beside the red.

SEVERAL OF THEM WERE GREEN AGAINST AN EARLIER DRAFT - the exact number is computed below from
`WAS_GREEN` rather than written into this sentence, because a count in the prose beside the run
that produced it is the drift RED-013 was corrected for, and this file has already carried three
different numbers for the same quantity. They were found by Fable in successive rounds, each against
the repairs made for the one before it, and the ROUND headings in the artefact are the only count of
them there is - a hand-typed count of the rounds drifted exactly like the counts above, which is why
one is not written here. They are of two kinds. Some are sentences a real editor would write while
softening a promise: `a single call`, `a single lookup`, `a couple of requests`, `once`, `ninety
HTTP requests` moved past a `</p>`. The rest are holes in what the gate could READ, where it went
green over copy it never saw at all. The first kind is why the gate counts NUMERALS rather than
nouns: the nouns a softening sentence might use cannot be enumerated, and the numbers a page may
state can. The second kind is why what counts as "the copy" is the hardest part of this gate.

THE SUBJECT IS A NUMBER WRITTEN IN THREE FILES - `CALLS_PER_PROBE` in `src/prober/prober.py`, the
copy of `web/src/pages/Apply.tsx`, and a sentence in `docs/WHY_GET_VERIFIED.md` - so mutations are
applied to all three, and the ones that matter most move a single copy and leave the others.

WHY THE FILES ARE MUTATED AND NOT COPIES OF THEM. The gate reads these files, so they are the
source under test. A mutation applied to a temporary copy would establish that the harness can fail
on a string, which is not the claim.

IT WRITES THE ARTEFACT ITSELF rather than being redirected into it: a shell truncates its target
before Python starts, so every refusal below would empty the committed artefact on its way to
declining to replace it - the defect RED-017's generator shipped and names.

WHAT IT REFUSES TO WRITE THE ARTEFACT OVER, each inherited from RED-017 and RED-018 because each
caught a real draft there:
  * a mutation whose anchor is not unique, or whose marker does not appear in every file it
    touched - an edit that did not land is a transcript about the pristine files;
  * a mutation that does not turn the suite red - a gate unarmed against the edit it is filed
    under is the whole subject;
  * a TRUE REWRITE that does turn the suite red - the false-red direction, and the finding that
    forced this section to exist;
  * a pytest that did not RUN. Only exit 1 is a suite that ran and failed; any other nonzero is an
    instrument that asserted nothing, and reading it as "red" is invariant 1 inside the tool kept
    to defend invariant 1;
  * a mutation that kills either INSTRUMENT CONTROL - the comment stripper, and the check that
    conditionally-rendered copy survives extraction. Every assertion reads extracted source, and a
    dead extractor fails the suite while establishing nothing about what the page says;
  * two mutations the operator could not tell apart. RED-018 compared the set of FAILED lines; with
    parametrised assertions that would have refused this file for distinctions anyone can see, so
    the signature here is the failing tests AND the assertion text printed under them - what the
    person meeting the red actually reads;
  * a file not restored byte for byte, or a suite not green afterwards.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTEFACT = ROOT / "evidence" / "RED-019-an-offer-narrower-than-what-arrives.txt"
SUITE = "tests/test_apply_names_the_probe_cost.py"

FORM = Path("web/src/pages/Apply.tsx")
PROBER = Path("src/prober/prober.py")
DOC = Path("docs/WHY_GET_VERIFIED.md")

# THE CONTROLS MUST BE SOMETHING NO MUTATION IN THIS FILE IS ABOUT (RED-018's correction). Neither
# edit below touches a comment or the extractor, so a red from either of these two would mean the
# instrument died rather than that a property was removed.
CONTROLS = ("test_the_stripper_removes_the_explanation_and_keeps_the_copy",
            "test_the_extractor_keeps_the_copy_that_is_conditionally_rendered")

TICKING = "                  Ticking this records the question."

# The copy as it stood before T-A2-5: one operation, no count, every word of it true in the
# prober's unit of account.
OFFER_NOW = """                  One operation exists today: we attempt to use a path you tell us is closed, and
                  report whether your running system actually refuses it &mdash; which your
                  repository cannot show. That one operation costs your origin three requests. We
                  ask a path you publish as public, to establish that your server answers us at
                  all; a path that cannot exist, to learn what your server says about a path that
                  is simply not there; and then the closed path itself. Without those two controls
                  a refusal is not a measurement, so they are part of the operation and not extras.
                  Ticking this records the question. It is answered with a document naming the
                  action, the paths, a ceiling on how often &mdash; which all three requests count
                  against &mdash; what must not be affected, who answers for damage, what stops the
                  run and how you revoke it, and nothing is sent at your systems before you sign
                  it."""

OFFER_BEFORE = """                  {/* MUTATION: the copy as it stood before T-A2-5 */}
                  One operation exists today: we attempt to use a path you tell us is closed, and
                  report whether your running system actually refuses it &mdash; which your
                  repository cannot show. Ticking this records the question. It is answered with a
                  document naming the action, the paths, a ceiling on how often, what must not be
                  affected, who answers for damage, what stops the run and how you revoke it, and
                  nothing is sent at your systems before you sign it."""

DOC_COUNT = """  **One operation is three requests to your origin**, and that is the number to judge us by, since
  it is the one your logs will show. We ask a path you publish as public, to establish that your
  server answers us at all; a path that cannot exist, to learn what your server says about a path
  that is simply not there; and then the closed path itself. Without those two controls a refusal
  is not a measurement — a 403 aimed at our client, or a 404 from a host that serves 404 to
  everything, would otherwise be published as your control working. All three count against the
  ceiling in the mandate, and a probe that cannot afford all three does not run at all rather than
  running half of itself. `CALLS_PER_PROBE` in `src/prober/prober.py` is where that number lives
  and `tests/test_apply_names_the_probe_cost.py` fails the build if the intake form and the code
  stop agreeing on it."""

CONFIRMATION = """            <p className="mt-4 text-sm text-[var(--color-ink-2)]">
              <strong>You asked about an active-probing mandate.</strong> Nothing is authorised by
              this form and nothing will be sent at your systems. What happens next is that the
              operator writes to you with a document to agree: it names the one action and the
              three requests it spends on your origin, the paths, a ceiling on how often, what
              must not be affected, who answers for damage, what stops the run, and how you revoke
              it. No request runs before you have signed it.
            </p>"""

CONFIRMATION_SPLIT = """            <p className="mt-4 text-sm text-[var(--color-ink-2)]">
              {/* MUTATION: one paragraph split into two, the count moved past the terminator */}
              <strong>You asked about an active-probing mandate.</strong> Nothing is authorised by
              this form and nothing will be sent at your systems.
            </p>
            <p className="mt-4 text-sm text-[var(--color-ink-2)]">
              What happens next is that the operator writes to you with a document to agree: it
              names the one action and the ninety HTTP requests it spends on your origin, the
              paths, a ceiling on how often, what must not be affected, who answers for damage,
              what stops the run, and how you revoke it. No request runs before you have signed it.
            </p>"""

DOC_MANDATE = "  It requires an explicit mandate"

# The opening tag of the option's description, where a tooltip would be hung.
LIE = "In practice only one request ever reaches your server."

CONFIRMATION_OPEN = """            <p className="mt-4 text-sm text-[var(--color-ink-2)]">
              <strong>You asked about an active-probing mandate.</strong>"""

RADIO = '<input type="radio" name="mandate" value="active" className="mt-1" />'

IMPORTS = 'import { Page, Strip } from "../components/Chrome";'

SPAN = ('<span className="block text-xs text-[var(--color-ink-3)]">\n'
        '                  One operation exists today')


def softener(sentence: str) -> tuple[Path, str, str]:
    """A reassuring line added to the option, which is how every one of these was actually found."""
    return (FORM, TICKING, f"                  {{/* MUTATION */}}\n                  {sentence}\n"
            + TICKING)


MUTATIONS = [
    (
        "1-the-offer-that-counts-operations-and-not-requests",
        "THE STATE T-A2-5 FOUND, restored word for word. Every sentence here is true: there is one "
        "operation, it is an attempt on a path the subject says is closed, and the mandate that "
        "follows names paths in the plural and a rate ceiling. What the person deciding is not "
        "told is that the one operation puts THREE requests into their logs. The offer is narrower "
        "than the artefact, which is the direction nobody audits - a claim too modest reads as "
        "care.\n"
        "#\n"
        "# IT ALSO PROVES THE PRESENCE RULE IS SCOPED TO THE OPTION. After it lands, `three "
        "requests` still appears twice in `Apply.tsx` - in the confirmation screen and in the "
        "file's own docstring - so a whole-file search for the number is GREEN over exactly the "
        "defect this task exists to close.",
        [(FORM, OFFER_NOW, OFFER_BEFORE)],
    ),
    (
        "2-the-constant-moves-and-the-page-keeps-the-old-number",
        "THE DRIFT, AND IT IS NOT HYPOTHETICAL: this constant was 2 until Fable found that a probe "
        "without a negative control cannot tell a withheld path from one that was never there. The "
        "next such finding adds a fourth request, the page is not open in the editor at the time, "
        "and `/apply/` goes on promising three - a number that was measured once and is now a "
        "guess. Nothing on either side of this pair is wrong in isolation, which is why the "
        "missing thing was the comparison and not a value (D-20).",
        [(PROBER, "CALLS_PER_PROBE = 3",
          "CALLS_PER_PROBE = 4  # MUTATION: a fourth request, page untouched")],
    ),
    (
        "3-two-counts-in-one-offer",
        "THE HALF-DONE EDIT, in the promise's own noun. A later hand adds a reassuring sentence and "
        "the option states three requests in one place and one in another. The count is present, so "
        "an assertion that only asked whether a number was there is green; the applicant reads two "
        "promises and cannot tell which of them we will keep.",
        [softener("In practice one request is usually all it takes.")],
    ),
    (
        "4-the-option-withdrawn-and-the-gate-left-standing",
        "D-21 IN MINIATURE, AND IT IS THE FAILURE MODE OF EVERY GATE THAT READS A PAGE. The active "
        "option is withdrawn - a legitimate decision, taken once already - and this file stays "
        "behind. Scoped to a block that no longer exists, the honest outcome is a red saying the "
        "gate is now guarding nothing, not a green earned by having nothing to check. L-16: a gate "
        "pointed at something that moved reports clean forever.",
        [(FORM, '<input type="radio" name="mandate" value="active" className="mt-1" />',
          '{/* MUTATION: the option withdrawn */}\n'
          '              <input type="radio" name="mandate" value="passive-only" className="mt-1" />')],
    ),
    (
        "5-one-surface-corrected-and-the-other-left",
        "THE SAME OFFER, IN THE COPY THAT SAYS OF ITSELF THAT NOBODY RE-READS IT. "
        "`docs/WHY_GET_VERIFIED.md` carries this offer to the same stranger and its own closing "
        "sentence records that it was the last thing corrected twice already - once while there "
        "was no prober, once the day after. Correcting the form and leaving the document is not a "
        "smaller version of this defect; it is the version that survives, because the fixed copy "
        "is the one everybody looks at afterwards.",
        [(DOC, DOC_COUNT, "  <!-- MUTATION: the count removed from the document -->")],
    ),
    # --- 6 to 11: the six Fable produced against the first two drafts of this gate. Every
    # one of them was GREEN when applied, and every one is a promise an applicant reads and acts on.
    (
        "6-the-softener-that-says-call-instead-of-request",
        "ROUND ONE. The first draft counted `<number> request(s)` and nothing else, so the "
        "contradicting sentence walked past it by saying `call` - and nobody softening a promise "
        "reaches for the noun the promise was made in. GREEN against a gate whose docstring "
        "claimed to catch exactly this case.",
        [softener("In practice it is usually a single call and no more.")],
    ),
    (
        "7-the-constant-moves-and-the-confirmation-screen-stays-behind",
        "ROUND ONE. Three copies corrected and a fourth surface left standing: `CALLS_PER_PROBE` "
        "becomes 4, the option and the document are updated, and the confirmation shown to the "
        "applicant who ASKED FOR THE ACTIVE MANDATE still says three requests. That screen is the "
        "last thing they read before the operator writes to them with a document to sign. GREEN "
        "against a gate scoped to the fieldset and the document - and whose scoping comment NAMED "
        "this screen as a place a count could hide, one screen before permitting it.",
        [
            (PROBER, "CALLS_PER_PROBE = 3",
             "CALLS_PER_PROBE = 4  # MUTATION: a fourth request"),
            (FORM, "costs your origin three requests",
             "costs your origin four requests {/* MUTATION */}"),
            (FORM, "which all three requests count", "which all four requests count"),
            (DOC, "**One operation is three requests to your origin**",
             "**One operation is four requests to your origin**<!-- MUTATION -->"),
            (DOC, "All three count against the", "All four count against the"),
        ],
    ),
    (
        "8-the-softener-that-says-lookup",
        "ROUND TWO, and the reason this gate stopped counting nouns. The second draft answered "
        "round one by LENGTHENING the noun list - calls, hits, connections, round-trips - and "
        "Fable walked past the longer list with `lookup`. A list of synonyms is never finished, "
        "and the draft after this one counts numerals instead: `a single` is caught here whatever "
        "noun follows it.",
        [softener("In practice it is a single lookup and no more.")],
    ),
    (
        "9-the-count-with-no-number-in-it",
        "ROUND TWO, AND THE ONE NO NOUN LIST COULD EVER HAVE CAUGHT. `a couple of requests` uses "
        "the promise's own noun and hedges the number instead - and the quantifier list of the "
        "draft that had just been widened for nouns did not have it. Vague where the task demands "
        "a number, and it reads as candour.",
        [softener("In practice it is usually a couple of requests, no more.")],
    ),
    (
        "10-the-count-carried-by-an-adverb",
        "ROUND TWO, STRUCTURAL. `once` states a count and names no noun at all, so no lengthening "
        "of any noun list can reach it - the quantity is the whole phrase. This is the mutation "
        "that settles the design question: the gate must read numbers, because a number can be "
        "written without the thing it counts and a thing cannot be written without a name.",
        [softener("In practice your server hears from us once.")],
    ),
    (
        "11-the-paragraph-split-and-the-count-moved-past-the-terminator",
        "ROUND TWO, AND IT IS THE CLASS BEHIND ROUND ONE'S SECOND FINDING. The repair for that "
        "finding scoped a new assertion from `sent.asked === \"active\"` to the next `</p>`. "
        "Splitting one long paragraph into two is the most ordinary editorial change there is, and "
        "it moves the count out of the scope: the applicant is then told we will send NINETY "
        "requests at their production system and every assertion passes. The instance was fixed "
        "and the class - a count anywhere on that screen - was not, so the scan now reads the "
        "whole page and there is no terminator left to move past.",
        [(FORM, CONFIRMATION, CONFIRMATION_SPLIT)],
    ),
    # --- 12 to 14: round three, against the draft that answered rounds one and two. All green.
    (
        "12-a-declared-phrase-reused-to-promise-less",
        "ROUND THREE, AND THE ALLOWLIST WAS THE DOOR. The draft that answered rounds one and two "
        "declared the quantities this page is allowed to state - as a number plus at most one "
        "following word, compared as a SET. `only one` was granted for \"(always the read-only "
        "one)\" in the privacy list, so this sentence inherits the permission with no line added "
        "anywhere: the applicant is told that what reaches their production system is ONE request "
        "and the prober sends three. Five more of the same shape were green, one of them the same "
        "phrase on the confirmation screen itself. A declaration must SPAN its number inside its "
        "own sentence, and enclosure rather than membership is what the gate compares now.",
        [softener("What reaches your server is, in practice, only one.")],
    ),
    (
        "13-the-count-hidden-between-two-apostrophes",
        "ROUND THREE, IN THE EXTRACTOR RATHER THAN IN THE RULE. `_STRING` stripped `'...'` as well "
        "as double quotes, and prose does not know it is inside a program: everything between "
        "\"don't\" and \"won't\" was deleted before any assertion ran, and the count went with it. "
        "The visitor reads a promise of one request; the gate reads a sentence with a hole in it. "
        "This is the `{...}` failure of an hour earlier surviving one line away in the sibling "
        "stripper - and the instrument control written for that one could not catch it, because "
        "none of the four sentences it names contains an apostrophe.",
        [softener("We don't send more than one request, and we won't retry.")],
    ),
    (
        "14-the-adverbial-count-in-the-document",
        "ROUND THREE, IN THE SURFACE THAT STILL HAD THE WEAKER RULE. The document was held by a "
        "noun-based check while the page was held strictly, and `once` names no noun - so this "
        "sentence was green in an offer a stranger reads, with the limitation honestly written "
        "down in a docstring two files away. A named blind spot is still a blind spot (L-25), and "
        "the reader receives the same false sentence either way. The strict rule covers the whole "
        "section now; it cost eleven declarations and nothing else.",
        [(DOC, DOC_MANDATE,
          "  In practice your server hears from us once.  <!-- MUTATION -->\n\n" + DOC_MANDATE)],
    ),
    # --- 15 to 17: round four, against the draft that answered round three. All three green.
    (
        "15-the-multiplier-read-as-the-thing-being-counted",
        "ROUND FOUR, AND IT WAS WORTH A HUNDREDFOLD. `_QUANTITY` captures a numeral and ONE "
        "following word, and the number was read from the numeral alone - so `three hundred "
        "requests` parsed as the prober's own `three` with `hundred` sitting in the noun slot. "
        "Every rule agreed the page was correct while it told the applicant we would put three "
        "hundred requests into their logs. The multipliers had been added to `_NUMERALS` to catch "
        "`ninety`, and adding them created the one place they are invisible: behind an accepted "
        "number. `one hundred requests` reds, and only a multiplier after the right number was "
        "free - which is the flattering direction, again.",
        [(FORM, "costs your origin three requests",
          "costs your origin three hundred requests {/* MUTATION */}")],
    ),
    (
        "16-copy-that-reaches-the-page-through-a-constant",
        "ROUND FOUR, AND THE THIRD TIME THIS EXTRACTOR DROPPED COPY SILENTLY. Strings were "
        "stripped as configuration - class names, URLs - but a sentence can be a string AND what a "
        "visitor reads. `ISSUES` and `DECISION_LOG` on this very page are written exactly this "
        "way, so it is the ordinary way to add a line and not a contrivance. Declared here and "
        "rendered through `{REASSURANCE}`, the promise was invisible to all ten assertions. The "
        "removals are by ROLE now - technical attributes and addresses - because \"it is a "
        "string\" was never the property that made something unreadable.",
        [(FORM, 'import { Page, Strip } from "../components/Chrome";',
          'import { Page, Strip } from "../components/Chrome";\n'
          '// MUTATION: copy that reaches the page through a constant\n'
          'const REASSURANCE = "In practice only one request ever reaches your server.";')],
    ),
    (
        "17-the-count-that-satisfies-presence-without-being-visible",
        "ROUND FOUR, AND TWO EXTRACTORS OVER ONE FILE WERE THE CAUSE. `_page()` cleaned its text "
        "and `_option()` did not, so the scope that answers \"does the offer state the cost\" "
        "still contained attribute strings. An `aria-describedby` naming three requests therefore "
        "satisfied presence while the visible sentence was softened to `costs your origin very "
        "little` - the offer stated in our unit and hedged, which is the exact sentence T-A2-5 was "
        "opened to remove, standing on a green suite. One `_clean` now serves both, so presence "
        "and the strict rule cannot read two different pages out of one file.",
        [
            (FORM, '<input type="radio" name="mandate" value="active" className="mt-1" />',
             '{/* MUTATION */}\n'
             '              <input type="radio" name="mandate" value="active" className="mt-1"\n'
             '                     aria-describedby="costs three requests" />'),
            (FORM, "That one operation costs your origin three requests.",
             "That one operation costs your origin very little."),
            (FORM, "which all three requests count", "which the ceiling counts"),
        ],
    ),
    # --- 18 and 19: round five, against the draft that answered round four. Both green.
    (
        "18-the-count-that-lives-in-a-tooltip",
        "ROUND FIVE, AND IT IS ROUND FOUR'S FINDING SURVIVING ITS OWN REPAIR. Unifying the "
        "extractor made presence and the strict rule read the same string - but the property that "
        "mattered was never \"the same text\", it was \"the text a visitor reads\", and the new "
        "line was drawn by ROLE with `title` on the copy side. A tooltip is read by somebody "
        "hovering a mouse: not on touch, not from a keyboard, not by anyone who simply reads the "
        "page. So the count moved into `title` and the visible sentence was softened to `costs "
        "your origin very little` - the offer stated in our unit and hedged, which is the sentence "
        "T-A2-5 was opened to remove, on a suite green in all eleven assertions. The rules read "
        "JSX text nodes now, and an attribute is not one.",
        [
            (FORM, SPAN, SPAN.replace('ink-3)]">', 'ink-3)]" title="three requests">')
             .replace("One operation exists today",
                      "One operation exists today {/* MUTATION */}")),
            (FORM, "That one operation costs your origin three requests.",
             "That one operation costs your origin very little."),
            (FORM, "which all three requests count", "which the ceiling counts"),
        ],
    ),
    (
        "19-the-tooltip-that-contradicts-the-count",
        "THE OTHER HALF OF THE SAME DISTINCTION, and it pulls the opposite way. A readable "
        "attribute may not be how the page COMPLIES with stating the cost - mutation 18 - and it "
        "may not CONTRADICT the cost either, which is what this one does: the visible copy is "
        "correct and the tooltip says ninety. Excluding attributes outright would have closed 18 "
        "and opened this, so `_page` gathers them for the strict rule while `_option` does not see "
        "them at all. Two rules that would each look like the other's bug if only one were "
        "written.",
        [(FORM, SPAN, SPAN.replace('ink-3)]">', 'ink-3)]" title="ninety requests">')
          .replace("One operation exists today", "One operation exists today {/* MUTATION */}"))],
    ),
    # --- 20 and 21: round six, against the draft that answered round five. Both green.
    (
        "20-copy-rendered-by-a-ternary-of-two-strings",
        "ROUND SIX. An expression whose branches are plain strings contains no angle bracket, so "
        "the text-node scan captured it as a text node and then deleted the whole `{...}` - both "
        "sentences with it. The page's existing branches survived only by an accident of style: "
        "they are written `{d ? (<>...</>) : (<>...</>)}`, which contains `<`, so the outer "
        "expression is not a text node and the inner text is captured separately. Rewrite them as "
        "strings - the smaller and more ordinary form - and the copy vanishes. Fourth silent drop "
        "by this extractor, third consecutive round.",
        [(FORM, CONFIRMATION_OPEN,
          '            <p className="mt-4 text-sm text-[var(--color-ink-2)]">\n'
          '              {/* MUTATION */}\n'
          '              {sent.delivered ? "' + LIE + '" : "' + LIE + '"}\n'
          '              <strong>You asked about an active-probing mandate.</strong>')],
    ),
    (
        "21-copy-declared-with-a-keyword-the-gate-was-not-told-about",
        "ROUND SIX, AND THE REASON THE RULE IS NOW ABOUT SHAPE RATHER THAN SYNTAX. The draft that "
        "answered round four read `^const NAME = \"...\"` because that is how `ISSUES` and "
        "`DECISION_LOG` are written on this page - so `export const`, `let`, an indented const, an "
        "object field, an array element and a template literal all went unread. `export const` is "
        "the ordinary React idiom for shared copy. The repair was fitted to two spellings instead "
        "of to the property, which is the shape of every extractor defect in this file.",
        [(FORM, IMPORTS,
          IMPORTS + '\n// MUTATION\n'
          'export const NOTE = "We send only one request in practice.";')],
    ),
    # --- 22 to 24: round seven, against the cut that answered round six. All three green.
    (
        "22-copy-in-a-component-that-never-says-return",
        "ROUND SEVEN, AND IT WALKED PAST THE CONTROL WRITTEN THAT ROUND TO PREVENT IT. An arrow "
        "component - the ordinary React idiom for a small presentational block - contains no "
        "`return` at all, so its copy sat outside every block the rules read. The control asserts "
        "the page yields at least two markup blocks and names a sentence from each; after this "
        "edit it still yields two and both sentences are still there, because a component that "
        "produces NO block does not change the count. It was written against a matcher that "
        "collapses blocks and is blind to copy that never makes one.",
        [(FORM, IMPORTS,
          IMPORTS + '\n// MUTATION\nconst Reassurance = () => (\n'
          '  <p className="mt-4 text-sm">' + LIE + '</p>\n);')],
    ),
    (
        "23-a-false-promise-two-words-long",
        "ROUND SEVEN. The prose-shape test required three tokens, and `Only once.` is two - a "
        "complete false promise, using a word that IS a count. Written as ordinary JSX text it "
        "reds; written as a string expression it was the literal collector's business, and the "
        "threshold excluded exactly the shortest softening sentences, which are the ones anybody "
        "actually writes.",
        [(FORM, TICKING, '                  {/* MUTATION */}\n'
          '                  {"Only once."}\n' + TICKING)],
    ),
    (
        "24-an-attribute-spelled-with-spaces-becomes-copy",
        "ROUND SEVEN, AND THE TOOLTIP FINDING REOPENED BY THE REPAIR TWO ROUNDS LATER. The "
        "attribute filter required `name=\"value\"` written tight, which is a house style rather "
        "than a rule of JSX. Spelled with spaces, the string was neither excluded from the "
        "literal collector nor gathered for contradiction: it became COPY, satisfied the presence "
        "rule, and let the visible sentence be softened to `costs your origin very little`. What "
        "separates an attribute from an assignment is not spacing - it is being inside a tag, and "
        "the scope of the option now starts at the tag's own `<` for the same reason.",
        [
            (FORM, RADIO,
             '{/* MUTATION */}\n'
             '              <input type="radio" name="mandate" value="active" className="mt-1"\n'
             '                     title = "costs three requests in total" />'),
            (FORM, "That one operation costs your origin three requests.",
             "That one operation costs your origin very little."),
            (FORM, "which all three requests count", "which the ceiling counts"),
        ],
    ),
]

# WHAT MUST NOT GO RED. Fable's finding against the second draft was a FALSE RED, not a false
# green: the gate demanded that the number sit immediately beside the noun, so the most natural
# true rewrite of the copy made it report that the offer stated no count at all. These four are
# the artefact of the repair.
GREEN_REWRITES = [
    (
        "an-adjective-between-the-number-and-the-noun",
        "`three HTTP requests` is the copy an editor would most likely write, and it made the "
        "second draft say the offer `does not say how many requests one probe sends` - over a page "
        "saying exactly that. The presence rule now allows up to three words between the number "
        "and the noun.",
        [(FORM, "costs your origin three requests", "costs your origin three HTTP requests")],
    ),
    (
        "another-adjective",
        "`three separate requests` - the same shape, and the word an editor reaches for when the "
        "point is that the controls are not the attempt.",
        [(FORM, "costs your origin three requests", "costs your origin three separate requests")],
    ),
    (
        "the-number-written-in-digits",
        "`3 requests` is as true as `three requests`, and a gate pinning the word form would be "
        "pinning a house style rather than a fact.",
        [(FORM, "costs your origin three requests", "costs your origin 3 requests")],
    ),
    (
        "a-different-true-noun",
        "`three round-trips` counts the same thing in a word the copy does not currently use. The "
        "gate accepts any noun once the number is right, which is the other half of counting "
        "numerals rather than nouns.",
        [(FORM, "costs your origin three requests", "costs your origin three round-trips")],
    ),
    (
        "an-ordinary-status-code-branch",
        "THE FALSE-RED DIRECTION, AND IT IS HOW A GATE GETS DELETED. A draft that read whole-file "
        "text nodes met this - an ordinary status guard, at this exact insertion point - with a "
        "red telling the author their status code was neither the prober's count nor a declared "
        "quantity, and inviting them to consider whether it was a promise we do not keep about "
        "somebody's production server. It is a status code. The same guard four lines earlier "
        "PASSED, because a `>` from `React.FormEvent<HTMLFormElement>` opened a pseudo-text-node "
        "that ran to the next `<`: an editor could not have formed a rule from it.",
        [(FORM, "      const d = await r.json().catch(() => ({}));",
          "      const d = await r.json().catch(() => ({}));\n"
          "      if (r.status === 429) { return; }")],
    ),
    (
        "an-ordinary-timeout-constant",
        "The same, in module scope rather than in a branch, and it is the sharper of the two "
        "because module constants are exactly where copy also lives - `ISSUES` and `DECISION_LOG` "
        "are written that way. A number here is code; a STRING here can be copy; the rules read "
        "text nodes and module strings, so this one is silent and mutation 16 is not.",
        [(FORM, 'import { Page, Strip } from "../components/Chrome";',
          'import { Page, Strip } from "../components/Chrome";\nconst RETRY_AFTER_MS = 3000;')],
    ),
    (
        "an-ordinary-loop",
        "The same defect with no status code in it at all. A `for` loop's bound was reported to "
        "its author as a count of requests we send to applicants, which is the sentence the strict "
        "rule prints - about a loop. The rules read the JSX return blocks now, and a function body "
        "is not one.",
        [(FORM, "    const form = new FormData(e.currentTarget);",
          "    const form = new FormData(e.currentTarget);\n"
          "    for (let i = 0; i < 3; i++) { void i; }")],
    ),
]

WAS_GREEN = frozenset({
    "6-the-softener-that-says-call-instead-of-request",
    "7-the-constant-moves-and-the-confirmation-screen-stays-behind",
    "8-the-softener-that-says-lookup",
    "9-the-count-with-no-number-in-it",
    "10-the-count-carried-by-an-adverb",
    "11-the-paragraph-split-and-the-count-moved-past-the-terminator",
    "12-a-declared-phrase-reused-to-promise-less",
    "13-the-count-hidden-between-two-apostrophes",
    "14-the-adverbial-count-in-the-document",
    "15-the-multiplier-read-as-the-thing-being-counted",
    "16-copy-that-reaches-the-page-through-a-constant",
    "17-the-count-that-satisfies-presence-without-being-visible",
    "18-the-count-that-lives-in-a-tooltip",
    "19-the-tooltip-that-contradicts-the-count",
    "20-copy-rendered-by-a-ternary-of-two-strings",
    "21-copy-declared-with-a-keyword-the-gate-was-not-told-about",
    "22-copy-in-a-component-that-never-says-return",
    "23-a-false-promise-two-words-long",
    "24-an-attribute-spelled-with-spaces-becomes-copy",
})
"""The mutations that PASSED a draft of the gate before the draft that ships. The header counts
this set rather than stating a number, and `main` refuses to run if a name here is not a mutation -
otherwise renaming one would quietly shrink a claim this file makes about its own thoroughness."""

HEADER = """# RED-019 - an offer narrower than what arrives at the applicant's server
#
# Produced by evidence/RED-019-generator.py, checked in beside this file so the runs below can be
# repeated rather than believed (L-26). It establishes that the gate landing with T-A2-5 -
# tests/test_apply_names_the_probe_cost.py - CAN fail in each of the {n_total} directions it holds,
# and that it does NOT fail on {n_true} true rewrites of the same copy.
#
# {n_green} OF THE {n_total} WERE GREEN against an earlier draft of that gate. Fable produced them in
# successive rounds of refutation, each round against the repairs made for the one before it. The
# ROUND headings below are the only count of those rounds: a number for them stood in this sentence
# saying TWO over an artefact whose own headings reach SEVEN, and it was wrong because it was typed
# while there were fewer - the same drift, in the same pair, that the two counts above are computed
# to avoid. They are computed from the mutation table below, not typed here: this file carried three
# different numbers for that quantity while it was being written, which is the drift RED-013 exists
# over. Nor is every green one a softening sentence, which is what that sentence also claimed. Some
# are: a real editor writes them while making a promise smaller. The rest are holes in what the gate
# could READ - a constant moved with a surface left standing, and extractor after extractor dropping
# copy silently - where the suite went green over a promise nobody could see.
#
# WHAT THE GATE IS FOR. `/apply/` told a stranger that "one operation exists today: we attempt to
# use a path you tell us is closed". True in the prober's unit of account, and the wrong unit for
# the page: src/prober/prober.py spends CALLS_PER_PROBE = 3 requests per probe - a positive
# control, a negative control and the attempt - all three on the subject's origin, all three
# counted against the ceiling their mandate sets. The offer was therefore MODEST beyond the
# artefact, which is the direction nobody checks: a claim that understates reads as care, and the
# person it misleads is the one deciding whether we may touch their production system.
#
# WHY THE GATE COUNTS NUMERALS AND NOT NOUNS, which is the whole story of its three drafts. Draft
# one matched `<number> request(s)`; mutation 6 walked past it saying `call`. Draft two answered
# with a longer noun list - calls, hits, connections, round-trips - and mutation 8 walked past THAT
# saying `lookup`, mutation 9 hedged the number instead with `a couple of`, and mutation 10 wrote
# the count as an adverb with no noun at all: `your server hears from us once`. The nouns a
# softening sentence might use cannot be enumerated. The numbers a page may state can, and they are
# now written down: every quantity in this copy is either the prober's number or one the gate has
# been told about, so a number nobody looked at is a red on the page where a stranger decides.
#
# THE NUMBER LIVES IN THREE FILES, so the gate is a comparison and the mutations move one copy at a
# time: one empties the page and leaves the constant, one moves the constant and leaves the page,
# one empties the document and leaves the page. No file is wrong on its own in any of those cases.
# What was missing was never the value - it was the comparison.
#
# THE MUTATIONS, IN ORDER. 1, the pre-T-A2-5 copy restored. 2, CALLS_PER_PROBE moved to 4 with the
# page untouched - the drift that will actually happen, since this constant was 2 until Fable found
# the negative control. 3, a second and contradicting count in the option. 4, the option withdrawn
# as D-21 once withdrew it, where the only honest outcome is a red saying the gate now guards
# nothing. 5, the form corrected and the document left behind - the copy whose own last sentence
# records that it is always the last thing corrected. 6, 8, 9 and 10, four softening sentences that
# each walked past a draft of this gate: `a single call`, `a single lookup`, `a couple of requests`
# and the adverbial `once`. 7, the whole drift performed carefully - constant, option and document
# moved to four - with the confirmation screen still saying three. 11, that same confirmation
# paragraph split in two so the count lands past the `</p>` a previous draft scoped to, telling the
# applicant we will send ninety requests at their production system. 12, a declared phrase reused
# verbatim to promise less, back when the allowlist granted `only one` everywhere it appeared. 13,
# a count hidden between two apostrophes, deleted by the string stripper before any rule ran. 14,
# the adverbial `once` in the document, which the weaker rule it then had could not see. 15, `three
# hundred requests` read as the prober's own `three`, because a multiplier sat where the noun was
# expected. 16, copy declared as a string constant and rendered through an expression, invisible to
# an extractor that treated every string as configuration. 17, an `aria-describedby` satisfying
# "the offer states the cost" while the visible sentence read `costs your origin very little` - two
# extractors over one file, disagreeing. 18, the same sentence with the count moved into a `title`
# tooltip, which the repair for 17 permitted because it drew the line by role and a tooltip looked
# like copy - read by a mouse, by nobody on touch or a keyboard. 19, the opposite half: a tooltip
# that CONTRADICTS a correct visible count, which excluding attributes outright would have opened.
#
# THE RULES READ JSX TEXT NODES NOW, plus copy declared as a module constant, plus the readable
# attributes for contradiction only. An attribute is not a text node, so 18 cannot recur; neither
# is a status code, which is what mutations 15 to 17's repair had made the build red over.
#
# AND THE RUNS THAT MUST STAY GREEN. `three HTTP requests`, `three separate requests`,
# `3 requests` and `three round-trips` are all true, and the second draft went RED on the first of
# them - telling an editor the offer stated no count while it stated the right one. A gate that
# reds over truthful copy is walked past exactly as fast as one that greens over lies (L-5), so
# those four runs are part of this evidence and not a footnote to it.
#
# WHAT THE GENERATOR REFUSES TO WRITE THIS FILE OVER:
#
#   * a mutation that does not go red, or whose marker does not appear in EVERY file it touched;
#   * a true rewrite that does go red - the false-red direction, which is why that section exists;
#   * a pytest that did not RUN - only exit 1 is a suite that ran and failed;
#   * a mutation that kills either INSTRUMENT CONTROL: the comment stripper, and the check that
#     conditionally-rendered copy survives extraction. The second control exists because the
#     extractor DID fail that way for an hour - `{...}` stripping deleted the confirmation screen
#     wholesale, so the page scan ran over a page with no confirmation on it, which is the surface
#     the scan had just been widened to cover;
#   * two mutations the reader could not tell apart - the signature is the failing tests AND the
#     assertion text printed under them, which is what forced the gate to quote the offending
#     phrase rather than just its number;
#   * a file not restored byte for byte, or a suite not green afterwards.
#
# The diff blocks are printed from the same strings that perform the edits, so the prose and the
# edit cannot disagree.
#
# Everything below each `$` line is the output of the command shown, with TWO substitutions, named
# here because an unnamed one would make this file's own claim false: object addresses are written
# as `0xADDR` and the run duration as `in Ns`. Both change between identical runs, and L-26 asks a
# reader to re-run this and compare - which they cannot do if a faithful reproduction always
# differs. Nothing else is altered.
#
"""

BAR = "# " + "=" * 92


def pytest_run() -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "pytest", SUITE, "-q"],
                          cwd=ROOT, capture_output=True, text=True)


ADDRESS = re.compile(r"0x[0-9a-f]{6,}")
DURATION = re.compile(r"\bin \d+\.\d+s\b")


def transcript(run: subprocess.CompletedProcess) -> str:
    """The run's output with the two things that change between identical runs made constant.

    L-26 asks a reader to re-run this and compare. They cannot: pytest prints object addresses
    (`<function _option at 0x7f2c...>`) and a wall-clock duration, so a faithful reproduction still
    produces a diff - and a reader who is taught that the diff is always noise stops reading it.
    These two substitutions are named here and in the artefact's header; everything else below a
    `$` line is verbatim.
    """
    return DURATION.sub("in Ns", ADDRESS.sub("0xADDR", run.stdout + run.stderr))


def signature(stdout: str) -> tuple[str, ...]:
    """What the person meeting this red would read: which tests failed, and what they said."""
    return tuple(sorted(
        ln.rstrip() for ln in stdout.splitlines()
        if ln.startswith("FAILED ") or ln.lstrip().startswith("E ")))


def apply(edits, pristine):
    """Write every edit, returning the files touched. Anchors are counted against the text as it
    stands after the previous edit, so two edits to one file cannot silently overwrite each other."""
    touched, mutated = [], dict(pristine)
    for target, old, new in edits:
        if mutated[target].count(old) != 1:
            raise SystemExit(f"anchor found {mutated[target].count(old)} times in {target}")
        mutated[target] = mutated[target].replace(old, new)
        if target not in touched:
            touched.append(target)
    for target in touched:
        (ROOT / target).write_text(mutated[target], encoding="utf-8")
    return touched


def restore(touched, pristine, name):
    for target in touched:
        (ROOT / target).write_text(pristine[target], encoding="utf-8")
        if (ROOT / target).read_text(encoding="utf-8") != pristine[target]:
            raise SystemExit(f"{name}: {target} was NOT restored; stopping")


def diff_block(edits):
    return "\n#\n".join(
        "\n".join(f"# - {ln}" for ln in old.split("\n"))
        + "\n" + "\n".join(f"# + {ln}" for ln in new.split("\n"))
        for _, old, new in edits)


def main(argv: list[str]) -> int:
    names = {name for name, _, _ in MUTATIONS}
    unknown = sorted(WAS_GREEN - names)
    if unknown:
        # A NAME IN `WAS_GREEN` THAT IS NOT A MUTATION would silently shrink the count this file
        # prints about its own thoroughness - a claim getting weaker with nothing to show for it.
        raise SystemExit(f"WAS_GREEN names mutations that do not exist: {unknown}")
    header = (HEADER.replace("{n_green}", str(len(WAS_GREEN)))
                    .replace("{n_true}", str(len(GREEN_REWRITES)))
                    .replace("{n_total}", str(len(MUTATIONS))))
    pristine = {p: (ROOT / p).read_text(encoding="utf-8") for p in (FORM, PROBER, DOC)}
    out, seen = [header], {}
    try:
        for n, (name, prose, edits) in enumerate(MUTATIONS, start=1):
            touched = apply(edits, pristine)
            # `-H` and not plain `-n`: grep omits the filename when handed exactly one file, so a
            # single-file mutation would produce lines the per-file check below could not
            # attribute, and every red here would be refused for an edit that had landed.
            grep = subprocess.run(["grep", "-Hn", "MUTATION", *(str(t) for t in touched)],
                                  cwd=ROOT, capture_output=True, text=True)
            run = pytest_run()
            restore(touched, pristine, name)

            targets = " ".join(str(t) for t in touched)
            marked = {ln.split(":", 1)[0] for ln in grep.stdout.splitlines()}
            for target in touched:
                if str(target) not in marked:
                    raise SystemExit(
                        f"{name}: no MUTATION marker in {target} - that file's edit did not land, "
                        "so the run below is a transcript of a mutation that ran in part")
            if run.returncode == 0:
                raise SystemExit(f"{name} did NOT go red: the gate is unarmed against it")
            if run.returncode != 1:
                raise SystemExit(
                    f"{name}: pytest exited {run.returncode}, which is not a suite that ran and "
                    "failed. A red must be an assertion, never an instrument that did not run")
            for control in CONTROLS:
                if control in run.stdout:
                    raise SystemExit(
                        f"{name} killed an instrument control ({control}): the extractor stopped "
                        "working, so this red is about a broken instrument and not about what the "
                        "page says")
            sig = signature(run.stdout)
            if sig in seen:
                raise SystemExit(f"{name} and {seen[sig]} print the SAME red")
            seen[sig] = name

            out.append(
                f"{BAR}\n# RED {n}. In {targets}.\n# {prose}\n#\n{diff_block(edits)}\n#\n"
                f"# $ grep -Hn 'MUTATION' {targets}\n"
                + "".join(f"# {ln}\n" for ln in grep.stdout.splitlines())
                + f"#\n# $ python3 -m pytest {SUITE} -q\n" + transcript(run) + "\n")

        out.append(f"{BAR}\n# TRUE REWRITES, WHICH MUST NOT GO RED. The finding that put this "
                   "section here was a FALSE RED:\n# a gate that reds over correct copy is walked "
                   "past exactly as fast as one that greens over\n# lies, and the second draft of "
                   "this gate did both in the same experiment.\n#\n")
        for n, (name, prose, edits) in enumerate(GREEN_REWRITES, start=1):
            touched = apply(edits, pristine)
            run = pytest_run()
            restore(touched, pristine, name)
            if run.returncode != 0:
                raise SystemExit(f"true rewrite {name} went RED: the gate is pinning a wording "
                                 "rather than a fact, and would teach the next editor to disable "
                                 f"it\n{run.stdout}")
            out.append(
                f"{BAR}\n# GREEN {n}. {name}. In {' '.join(str(t) for t in touched)}.\n# {prose}"
                f"\n#\n{diff_block(edits)}\n#\n# $ python3 -m pytest {SUITE} -q\n"
                + transcript(run) + "\n")
    finally:
        for p, text in pristine.items():
            (ROOT / p).write_text(text, encoding="utf-8")

    green = pytest_run()
    if green.returncode != 0:
        raise SystemExit("the restored files are not green; the reds above prove nothing")
    out.append(f"{BAR}\n# GREEN, on the restored files, so the reds above are known to be the "
               "mutations' doing\n# and not a suite that fails on everything.\n#\n"
               f"# $ python3 -m pytest {SUITE} -q\n" + transcript(green))

    summary = f"{len(MUTATIONS)} mutations, all red, all distinct; {len(GREEN_REWRITES)} true " \
              "rewrites, all green"
    if "--check" in argv:
        print(f"{summary}; nothing written")
        return 0
    tmp = ARTEFACT.with_suffix(".txt.new")
    tmp.write_text("".join(out), encoding="utf-8")
    tmp.replace(ARTEFACT)
    print(f"{ARTEFACT.relative_to(ROOT)}: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
