"""T-A2-5 - the offer on /apply/ names what a probe actually spends on the applicant's origin.

THE DEFECT THIS HOLDS SHUT. The active-probing option said "One operation exists today: we attempt
to use a path you tell us is closed" and said nothing else about size. That sentence is true in the
prober's unit of account - `ACTION` is one action and there is exactly one - and it is the wrong
unit for the page it stands on. `src/prober/prober.py` spends `CALLS_PER_PROBE` requests on the
subject's origin per probe: a positive control, a negative control and the attempt itself. The
stranger reading this form is deciding whether we may reach their live system, and what reaches it
is requests. An offer stated in a unit that makes it sound smaller than it is, on the one screen
where somebody commits to something, is this project's own defect class - a claim narrower than the
artefact rather than wider, which is the direction nobody checks.

WHY A GATE AND NOT A CAREFUL EDIT. The number is now written in three places: a constant in Python,
a word in JSX, and a sentence in the document that carries the same offer to the same stranger. That
is L-2, and the failure mode is not that today's copy is wrong - it is that `CALLS_PER_PROBE`
changes for a good reason (it was 2 until Fable found that a probe without a negative control cannot
tell a withheld path from one that was never there) and the prose keeps quoting the old number for
as long as nobody happens to reread all three files. The comparison is the thing that was missing,
not the value that differed (D-20).

THE GATE COUNTS NUMERALS, NOT NOUNS, AND THAT IS THE WHOLE LESSON OF ITS FIRST TWO DRAFTS. Draft
one matched `<number> request(s)`; Fable walked past it with "in practice it is usually a single
CALL". Draft two answered with a longer list of nouns - calls, hits, connections, round-trips - and
Fable walked past THAT with "a single LOOKUP", then with "once", which carries a count and has no
noun at all. Synonyms are unbounded and no list of them is ever finished; the numbers a page may
state are few and can be written down. So the rule is inverted: on the page where a stranger
decides, EVERY quantity is either the prober's number or one this file names, and a new number
appearing anywhere in that copy is a red until a human says what it counts. That is a real cost -
an unrelated edit that adds a number will fail the build - and it is the cost that buys the
property, because the alternative is a gate that holds against the synonyms somebody thought of.

WHAT EACH SCOPE OWES, and they are two different obligations:

  * PRESENCE (`_option`, `_cost_paragraph`) - the offer must state the cost where the offer is
    made. Silence is the state this task found, and a count in the privacy list at the foot of the
    form, or in this file's own docstring, would satisfy a whole-file search and leave it exactly
    where it was.
  * EVERY QUANTITY DECLARED (`_page`, `_offer_section`) - the strict rule, over the whole intake
    page and the whole offer section of the document. `_page` is the WHOLE page rather than the
    option block because Fable's third finding was that scoping to a block leaves the rest of the
    screen open: splitting the confirmation paragraph in two moved its count out of a
    `</p>`-terminated scope and the suite stayed green over "the ninety HTTP requests it spends on
    your origin". The document had a weaker noun-based rule for one round and it was the wrong
    trade - it could not see "your server hears from us once", and a disclosed blind spot is still
    a blind spot (L-25). Stripping decision references and status codes is what makes the strict
    rule affordable over the document's prose; on the form, reading text nodes rather than the
    module is what makes it affordable there.

  A DECLARATION MUST SPAN THE NUMBER IN ITS OWN SENTENCE, and that is not a detail. The draft that
  declared bare keys - `one`, `two`, `only one` - granted them everywhere they appeared, and six
  false promises walked through without a line being added to the list, one of them on the
  confirmation screen: "in practice what reaches you is only one". Enclosure is checked now, so a
  permission can only be reused by reproducing a whole sentence around the number.

AND WHAT COUNTS AS THE COPY IS THE HARDEST PART OF THIS GATE, not the rules over it. Four drafts of
the extractor each dropped or admitted the wrong thing, and every one of them was green over a
promise: `{...}` stripping deleted the entire confirmation screen; `'...'` stripping ate the
sentence between two apostrophes; stripping every string deleted copy declared as a constant and
rendered through an expression; and keeping the module admitted `if (r.status === 429)` as a second
count, which is the false red that gets a gate switched off; and reading only `^const` strings
missed `export const`, `let`, an object field and a ternary of two string literals, which is how
shared copy is ordinarily written in React.

It reads the JSX RETURN BLOCKS - matched by parenthesis depth, so no function body is copy and a
status code cannot be reported as a promise - plus every string literal SHAPED LIKE PROSE wherever
it is written, because each attempt to name the copy-carrying syntax was fitted to the spellings
this page happens to use. `title`/`alt`/`aria-label`/`value` are read only for the strict rule and
never for presence: a tooltip may not contradict the count and may not be how the page complies
with stating it either. Instrument controls hold every one of those properties, two of them feeding
the extractor prose of their own so that no rewrite of the page can disarm them.

WHAT IS DELIBERATELY NOT PINNED. The wording, and the shape of the number. `three requests`,
`3 requests` and `three HTTP requests` are all true, so all three pass: the presence match allows
words between the number and the noun, which draft two forbade - it went red over `three HTTP
requests`, telling an editor the offer said nothing while it said exactly the right thing. A gate
that reds over a truthful rewrite teaches walking past it exactly as a false green does (L-5).

THE COST OF THE STRICT RULE, STATED RATHER THAN DISCOVERED. Copy that enumerates the three requests
one by one - "one call to a path you publish as public; one call to a path that cannot exist" - is
the clearest way to write them and it is a red until those phrases are added to `PAGE_QUANTITIES`
below. That is deliberate: the gate cannot tell a per-item count inside a correct total from a
second and contradicting total, and the safe direction is the one that makes a human look.

WHAT TIES THE CONSTANT TO BEHAVIOUR, so this is not a gate pinning prose to another piece of prose:
`tests/test_prober.py` asserts that a recording transport holds exactly `CALLS_PER_PROBE` calls
after a permitted probe. The chain the page's number hangs from is therefore copy -> constant ->
counted transport calls, and every link of it fails loudly.

HOW TO MAKE IT FAIL: change `CALLS_PER_PROBE` without touching the copy, state a second count
anywhere on the page in any words at all, take the count out of the option, or correct one surface
and not another. The red runs, and the true rewrites that must stay green beside them, are kept in
`evidence/RED-019-an-offer-narrower-than-what-arrives.txt`. Its generator marks which of them were
GREEN against an earlier draft of this file and counts them there; the number is not repeated here,
because a count written beside the artefact that produces it is what RED-013 was corrected for and
this pair has already carried three different values for it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.prober.prober import CALLS_PER_PROBE

# THE COMMENT STRIPPER IS IMPORTED RATHER THAN COPIED. It carries two edges Fable found - line
# comments matched as `(?<!:)//` so that a URL's own `//` does not swallow the rest of the line,
# and JSX comment blocks removed before block comments - and a second copy of it here would be a
# second thing to keep in step, inside the one file whose whole subject is two copies of a rule
# drifting apart.
from tests.test_intake_records_the_mandate_request import _code

ROOT = Path(__file__).resolve().parents[1]
FORM = ROOT / "web" / "src" / "pages" / "Apply.tsx"
DOC = ROOT / "docs" / "WHY_GET_VERIFIED.md"
"""THE SECOND SURFACE, AND IT ASKS TO BE HELD. `docs/WHY_GET_VERIFIED.md` is not a page a stranger
ticks a box on, and it carries the same offer in the same words - its own closing sentence says
this bullet "asked for the mandate in the present tense while there was no prober, then said the
opposite for one day, and both times it was the last copy to be corrected: this document IS the
offer, and it is the copy nobody re-reads". Fixing the form and leaving the document is how the
count would be right in one place and stale in the other by the end of the week."""

NUMBER_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven"}

# A count with no number in it is still a count, and it is how a softening sentence is actually
# written. `a couple of`, `a handful of`, `once` and `twice` all reached an earlier draft of this
# gate untouched; `once` and `twice` carry their number with no noun to attach it to, which is why
# the strict rule below is written over quantities rather than over nouns.
_HEDGES = ("a single", "just one", "only one", "no more than one", "a couple of", "a handful of",
           "a few", "several", "once", "twice", "dozens of")
_NUMERALS = (
    "one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen"
    "|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety"
    "|hundreds?|thousands?|dozens?|a dozen|"
    # `\d+` alone could not see `3k` or `3M`: `\b(\d+)\b` refuses a digit run followed by a
    # letter, so those produced no quantity at all. Three times now a numeral form nobody had
    # enumerated has walked through - `ninety`, `three hundred`, and this - which is the argument
    # for the shape of the whole rule rather than against it: the forms are finite and each one
    # closed stays closed. `3` still reads as `3`, so the accepted number is unaffected.
    r"\d[\d,]*(?:\.\d+)?[kKmM]?")
"""THE LIST RUNS PAST TEN BECAUSE IT STOPPED AT TEN AND SOMETHING WALKED THROUGH. Fable's
"the ninety HTTP requests it spends on your origin" was green against a draft whose numerals ended
at `ten`: an overstatement rather than an understatement, and still a false promise to somebody
deciding what may reach their production system. A list of the numbers a page might state is
finite, unlike a list of the nouns it might attach them to, and this is the whole reason the rule
counts numerals - so the list may not be the half-finished one."""

_MULTIPLIERS = frozenset({"hundred", "hundreds", "thousand", "thousands", "dozen", "dozens",
                          "million", "millions", "billion", "billions"})
"""Words that multiply the numeral in front of them. They are what `three hundred requests` is made
of, and reading `hundred` as the noun being counted is how that sentence passed as the prober's
`three`."""

_QUANTITY = re.compile(
    r"\b(" + "|".join(_HEDGES) + "|" + _NUMERALS + r")\b(?:\s+([\w-]+))?", re.IGNORECASE)

_INTERACTION = (r"requests?|calls?|hits?|connections?|round[- ]trips?|fetch(?:es)?|lookups?"
                r"|quer(?:y|ies)|pings?|visits?")
"""`attempts` and `gets` were here and came out: both are commoner as verbs, and the document says
"the prober does exactly one thing: **it attempts to use a path you tell us is closed**" - a true
sentence, with `one` three words to the left of a verb, reported as a wrong count of what we send.
A gate that reds over the offer's own description of itself is one nobody keeps."""
"""Nouns meaning "something landed in their logs". Used ONLY by the two rules that can afford to
name nouns - presence, where a missing noun costs a red on a true page and one line to fix, and
the document's weaker check. The strict rule does not consult this list, because the list is the
thing that could never be finished."""

# WHAT COMES OUT IS WHAT A PERSON READS, and each removal below is narrow for a reason paid for.
# Comments go first (they are this gate's own explanation), then the attributes and addresses that
# carry numerals nobody reads, then the plain JSX expressions. Everything else stays, INCLUDING
# ordinary string literals, because a string is not automatically configuration.
_TEXT_NODE = re.compile(r">([^<>]+)<")
"""WHAT A VISITOR READS IS WHAT SITS BETWEEN THE TAGS, and reading the module instead was two
defects at once.

The draft before this one removed technical attributes and kept the rest, drawing the line by ROLE
- which put `title` on the copy side. A tooltip is read by somebody hovering a mouse: not on touch,
not from a keyboard, not by anyone simply reading the page. So `title="three requests"` satisfied
"the offer states the cost" while the visible sentence said "costs your origin very little", which
is the exact sentence T-A2-5 exists to remove, standing on a green suite. In the other direction,
keeping the module meant the strict rule read the component's JavaScript: `if (r.status === 429)`
and `const RETRY_AFTER_MS = 3000` each turned the build red with a message about promises made to
applicants. A status code is not a promise, and a gate that says it is gets deleted (L-5).

Text nodes answer both at once. An attribute is not one, and neither is a status code."""

_COPY_ATTRIBUTE = re.compile(r'\b(?:title|alt|aria-label|value)\s*=\s*"([^"\n]*)"')
"""The attributes a person genuinely can read, gathered for the STRICT rule and deliberately not
for presence. A tooltip that CONTRADICTS the count is a false promise and must red; a tooltip that
SATISFIES the requirement to state the cost is the hole described above. May not contradict is one
rule; may be used to comply is another."""

_ADDRESS = re.compile(r'"(?:https?://|#|/)[^"\n\s]*"')
"""URLs, fragments and paths, wherever they are written. NO WHITESPACE, because an address has
none and a sentence does: `"#1 rule: only one request reaches you"` is copy that happens to start
with a fragment character, and the earlier pattern swallowed it whole. `#d-14-measurement-on-the-public-surface`
is a numeral in a link, not a promise."""

_STRING_WAS_STRIPPED_ONCE = """AND ORDINARY STRINGS ARE NOT TOUCHED, WHICH IS THE THIRD REPAIR TO
THIS EXTRACTOR AND THE ONE THAT NAMES THE CLASS.

It stripped every `"..."`, on the reasoning that strings are class names and URLs. Copy can be
both a string and what a visitor reads:

    const REASSURANCE = "In practice only one request ever reaches your server.";
    ...
    <p className="mt-4 text-sm">{REASSURANCE}</p>

Every rule passed and `"only one request" in _page()` was False - the third time this extractor
silently dropped the copy it exists to read, after `\\{[^{}]*\\}` deleted the confirmation screen
and after `'...'` ate the sentence between two apostrophes. `ISSUES` and `DECISION_LOG` on this
very page establish the const-then-render pattern, so it is the ordinary way to add a sentence and
not a contrivance. The removals are therefore by ROLE - technical attributes, addresses - rather
than by syntax, because "it is a string" was never the property that made something unreadable."""
_INNER_EXPR = re.compile(r"\{[^{}<]*\}")
"""`[^{}<]` AND NOT `[^{}]`, WHICH IS A BUG THIS FILE SHIPPED FOR AN HOUR. Every conditionally
rendered block on this page - the confirmation screen, the failure notice, the delivered/not
delivered branch - is a single `{...}` expression with no nested braces once the strings are gone,
so the wider pattern deleted all of them. The page scan then read a page with no confirmation
screen on it, which is the exact surface Fable had just found unguarded: an extractor that quietly
drops the copy it was widened to cover. Excluding `<` keeps anything containing JSX and removes
only the plain expressions - `{-1}`, `{ISSUES}`, `{" "}` - that carry numerals no visitor reads.
`test_the_extractor_keeps_the_copy_that_is_conditionally_rendered` is what stops it coming back."""
_ENTITY = re.compile(r"&[a-z]+;")

# Decision references, task ids and HTTP status codes: numerals in prose that count nothing. They
# are removed from the document's text rather than listed as permitted quantities, because the
# list would then need a new line every time a decision is cited - a gate whose cost falls on
# unrelated work is a gate somebody eventually deletes.
_REFERENCE = re.compile(r"\b(?:[A-Z]{1,4}-\d[\d.\-]*|ERC-?\d+|[45]\d\d)\b")


def _accepted() -> set[str]:
    """Every form of the prober's number a truthful page may use: the word and the digits."""
    return {NUMBER_WORDS[CALLS_PER_PROBE], str(CALLS_PER_PROBE)}


def _quantities(text: str) -> dict[str, str]:
    """Every quantity stated in `text`: the phrase as written, and the number it carries.

    The phrase is kept beside the number because a red naming `['a single call']` puts the editor
    in front of the sentence, while one naming `['one']` sends them hunting. A hedge with no
    number of its own - "a handful of" - is carried as itself, and is never an accepted count.
    """
    out: dict[str, str] = {}
    for m in _QUANTITY.finditer(text):
        head = " ".join(m.group(1).lower().split())
        phrase = " ".join(x for x in (m.group(1), m.group(2)) if x)
        number = {"a single": "one", "just one": "one", "only one": "one",
                  "no more than one": "one", "once": "one", "twice": "two"}.get(head, head)
        # A MULTIPLIER IS PART OF THE NUMBER, NOT THE THING COUNTED, and reading it as the thing
        # counted was worth a hundredfold. `three hundred requests` matched with `three` in the
        # number group and `hundred` in the following-word group, so the quantity read as the
        # prober's own three and every rule agreed the page was correct - while the applicant was
        # told we would put three hundred requests into their logs. The multipliers were added to
        # `_NUMERALS` to catch `ninety`, and adding them created a place where they are invisible.
        # Joined here, the compound is simply not the accepted number and must be declared.
        if (m.group(2) or "").lower() in _MULTIPLIERS:
            number = f"{number} {m.group(2).lower()}"
        out[" ".join(phrase.lower().split())] = number
    return out


def _states_the_count(text: str) -> bool:
    """Is the prober's number stated against a noun that means "we sent something"?

    Up to three words are allowed between the two, so `three HTTP requests` and `three separate
    requests` are read as what they are. Draft two demanded adjacency and went red over both.
    """
    numbers = "|".join(re.escape(n) for n in sorted(_accepted()))
    # THE LOOKAHEAD IS THE SAME MULTIPLIER DEFECT, in the rule that says the count is present.
    # Without it `three hundred requests` satisfies "the offer states the cost" - the strict rule
    # would still red, but the message a reader gets would say the page states the right number.
    multipliers = "|".join(sorted(_MULTIPLIERS))
    return re.search(rf"\b({numbers})\b(?!\s+(?:{multipliers})\b)\s+(?:[\w-]+\s+){{0,3}}?"
                     rf"({_INTERACTION})\b", text, re.IGNORECASE) is not None


def _declared_spans(text: str, declarations) -> list[tuple[int, int]]:
    """Where each declaration actually sits in `text`, as character ranges."""
    spans = []
    for phrase in declarations:
        start = 0
        while (i := text.find(phrase, start)) != -1:
            spans.append((i, i + len(phrase)))
            start = i + 1
    return spans


def _undeclared(text: str, declarations) -> list[str]:
    """Quantities in `text` that are neither the prober's number nor inside a declared sentence.

    ENCLOSURE, NOT MEMBERSHIP. The comparison is "does a declared phrase span this occurrence",
    not "is this occurrence's key in a set". A set of keys grants the key everywhere it appears,
    which is how six false promises passed an earlier draft without a line being added to it.
    """
    accepted = _accepted()
    spans = _declared_spans(text, declarations)
    stray = []
    for m in _QUANTITY.finditer(text):
        if _quantities(m.group(0)).get(" ".join(m.group(0).lower().split()), "") in accepted:
            continue
        if any(start <= m.start() and m.end() <= end for start, end in spans):
            continue
        # The context, not the phrase: an editor meeting this red has to find the sentence, and
        # `['one']` does not tell them which of the page's sentences it came from.
        stray.append("..." + " ".join(text[max(0, m.start() - 45):m.end() + 30].split()) + "...")
    return stray


def _strip_expressions(part: str) -> str:
    """Remove `{...}` expressions from ONE text node, repeatedly until none is left.

    Per node, and never over the joined text: joining first makes brace pairs that never existed
    in the source - a `{` from one node closing against a `}` from another - and the first version
    of this deleted the entire confirmation screen that way, which is the third time an extractor
    here quietly dropped the copy it was written to read.
    """
    previous = None
    while previous != part:
        previous, part = part, _INNER_EXPR.sub(" ", part)
    return part


_RETURNS_MARKUP = re.compile(r"(?:return|=>)\s*\(")
"""The two ways this file can hand markup back: an explicit `return (` and an arrow body `=> (`."""


def _jsx_blocks(source: str) -> list[str]:
    """Every `return ( ... )` in the module, matched by parenthesis depth.

    THE MARKUP IS THE ONLY PART OF THIS FILE THAT SPEAKS TO A VISITOR, and scanning the rest was
    the false red that would have got this gate deleted. Reading whole-file text nodes meant a `>`
    from `React.FormEvent<HTMLFormElement>` opened a pseudo-node running to the next `<`, so
    whether a numeral in `submit()` was read as a promise depended on where it fell between brace
    pairs: `if (r.status === 429)` passed four lines above and failed four lines below, and a `for`
    loop was reported to its author as a count of requests we send to applicants. An editor cannot
    form a rule from that, which is worse than a plain false red.

    Function bodies are outside every block returned here, so a status code is not copy and cannot
    be reported as one.

    `=> (` COUNTS AS A RETURN, and leaving it out was a whole screen wide. An arrow-function
    component - `const Reassurance = () => (<p>...</p>)` - is the ordinary React idiom for a small
    presentational block and contains no `return` at all, so its copy sat outside every block while
    the control written to catch exactly this stayed green: it asserts two blocks and finds two,
    because a component that produces no block does not change the count.
    """
    blocks, i = [], 0
    while (match := _RETURNS_MARKUP.search(source, i)) is not None:
        i = match.start()
        depth, j = 0, match.end() - 1
        while j < len(source):
            if source[j] == "(":
                depth += 1
            elif source[j] == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        block = source[i:j]
        # `() => ({})` is an arrow returning an object, not markup - `.catch(() => ({}))` on this
        # page. A block with no tag in it is code, and admitting it would put the module's own
        # values back among the copy, which is the false red this cut exists to end.
        if "<" in block:
            blocks.append(block)
        i = j
    return blocks


def _copy_literals(source: str) -> list[str]:
    """String literals SHAPED LIKE PROSE, wherever in the module they are written.

    A sentence can reach the page as a string, and every attempt to say WHICH strings by their
    spelling has been wrong: `^const` read `ISSUES` and `DECISION_LOG` because those are how this
    page happens to be written, and missed `export const`, `let`, an indented const, an object
    field, an array element and a template literal - `export const` being the ordinary React idiom
    for shared copy. And a ternary of two string literals inside JSX was captured as a text node
    and then deleted whole, taking both sentences with it.

    So the test is the SHAPE of the string rather than the syntax around it: at least two words, of
    which at least three fifths are ordinary words. TWO AND NOT THREE, because `{"Only once."}` is
    a complete false promise in two words and `once` is a count - the threshold that excluded it
    excluded exactly the shortest softening sentences, which are the ones anybody writes. `content-type`, `application/json`,
    `passive` and a URL are not; a sentence is. Today this returns nothing at all from
    `Apply.tsx` - every string in it is code - so the first prose one to appear is the one this
    was written for.
    """
    out = []
    for match in re.finditer(r'"((?:[^"\\\n]|\\.)+)"', source):
        tokens = match.group(1).split()
        words = [t for t in tokens if t.strip('.,;:!?()"’—-').isalpha() and len(t) >= 2]
        if len(tokens) >= 2 and len(words) >= 0.6 * len(tokens):
            out.append(match.group(1))
    return out


_TAG = re.compile(r"<[^>]*>")
_ATTRIBUTE_ASSIGNMENT = re.compile(r'[\w-]+\s*=\s*"[^"\n]*"')
"""An `=` in front of a string is what makes it an attribute rather than a sentence.

WITHOUT THIS, THE PROSE-SHAPE TEST READS ATTRIBUTES AS COPY - and `aria-describedby="costs three
requests"` is three words, all of them ordinary, so it satisfied the presence rule the moment
literals were admitted. That is round five's tooltip finding, reopened by the repair for round
six's, in the same edit. Attributes reach the strict rule through `_COPY_ATTRIBUTE` and reach
presence through nothing at all.

SPACES ARE ALLOWED AROUND THE `=`, AND WHAT SEPARATES AN ATTRIBUTE FROM AN ASSIGNMENT IS BEING
INSIDE A TAG - `_strip_attributes` applies this pattern only within `<...>`, never to the module. The first
version required none, on the reasoning that JSX attributes are written tight and JS assignments
are not - which is a house style, not a rule of the language. `title = "costs three requests"` was
then neither excluded from the literal collector nor gathered by `_COPY_ATTRIBUTE`, so it became
COPY: it satisfied presence, the visible sentence was softened to "costs your origin very little",
and the suite stayed green. That is the tooltip finding fully reopened by the repair for the one
after it. The lookbehind for `=` and a word character is what keeps `const NOTE = "..."` out of
this pattern - the version before that had no lookbehind and deleted the constant it was meant to
read."""


def _strip_attributes(markup: str) -> str:
    """Remove attribute values, and ONLY inside tags.

    `title = "costs three requests"` and `const NOTE = "a sentence"` are the same shape to a regex
    and opposite things to a reader: one is configuration a visitor never sees, the other is copy.
    The distinguishing feature is not the spacing - JSX allows either - it is which side of a `<`
    the assignment sits on. A pattern applied to the whole module deleted the constant it was
    written to read; one requiring tight `=` let a spaced attribute become copy and satisfy the
    presence rule. Both were caught by controls in the same run that introduced them.
    """
    return _TAG.sub(lambda m: _ATTRIBUTE_ASSIGNMENT.sub(" ", m.group(0)), markup)


def _visible(source: str) -> str:
    """What a visitor reads: the text in the markup, plus any copy carried by a string.

    Both halves are needed and each excludes what the other admits. Inside the markup, copy is the
    text between tags AND a string in an expression - a ternary of two sentences is the ordinary
    way to write a branch - but NOT an attribute value. Outside the markup, copy is any string
    shaped like prose, whatever keyword declared it, because every attempt to name the declaring
    syntax was fitted to the two spellings this page happens to use.
    """
    blocks = _jsx_blocks(source) or [source]
    markup = " ".join(blocks)
    outside = source
    for block in blocks:
        outside = outside.replace(block, " ")
    parts = [_strip_expressions(m.group(1)) for m in _TEXT_NODE.finditer(markup)]
    parts += _copy_literals(_strip_attributes(markup))
    parts += _copy_literals(outside)
    return " ".join(_ENTITY.sub(" ", _ADDRESS.sub(" ", " ".join(parts))).split())


def _page() -> str:
    """Everything the intake page says, in text and in the attributes a person can read.

    THE SCOPE IS THE PAGE AND NOT THE OPTION, and Fable's third finding is the reason. A scope
    that ended at `</p>` was escaped by splitting one paragraph into two - the most ordinary edit
    there is - and the count that moved past the terminator could then say anything. There is no
    terminator to move past here.

    The readable attributes are included HERE and not in `_option()`: this rule says no quantity may
    contradict the prober, and a tooltip is as capable of contradicting it as a sentence.
    """
    code = _code(FORM)
    markup = " ".join(_jsx_blocks(code))
    attributes = " ".join(m.group(1) for m in _COPY_ATTRIBUTE.finditer(markup))
    return _visible(code) + " " + " ".join(_ENTITY.sub(" ", attributes).split())


def _option() -> str:
    """The active option's own description - the sentences somebody reads before ticking the box."""
    code = _code(FORM)
    start = code.find('value="active"')
    assert start != -1, (
        'web/src/pages/Apply.tsx no longer offers a radio with value="active". If the active-'
        "mandate option was withdrawn again, withdraw or repoint this gate in the same commit "
        "rather than leaving it green over nothing - D-21 removed the option and left the rule "
        "behind it standing in three documents, which is how a repealed rule keeps enforcing."
    )
    # FROM THE START OF THE TAG, not from the attribute that identifies it. A slice beginning at
    # `value="active"` cuts the `<input` off its own opening bracket, so the tag has no `<...>` for
    # the attribute stripper to work inside - and `title="three requests"` on that element was read
    # as copy and satisfied the presence rule while the visible sentence said "very little". The
    # anchor is an attribute because that is what identifies the element; the scope is the element.
    start = code.rfind("<", 0, start)
    assert start != -1, "the active radio is not inside any element this gate can bound"
    end = code.find("</fieldset>", start)
    assert end != -1, "the active option is no longer inside a fieldset this gate can bound"
    # SLICED FROM THE SOURCE AND THEN CLEANED BY THE SAME FUNCTION THE PAGE USES. The anchors are
    # attributes, so they have to be found before the attributes are removed - but what is measured
    # afterwards must be the visitor's text, or presence and the strict rule are reading two
    # different pages out of one file.
    return _visible(code[start:end])


def _offer_section() -> str:
    """The active-probing section of `WHY_GET_VERIFIED.md`, to the next heading."""
    text = DOC.read_text(encoding="utf-8")
    start = text.find("Active probing is now offered")
    assert start != -1, (
        "docs/WHY_GET_VERIFIED.md no longer offers active probing. If the offer was withdrawn, "
        "withdraw this half of the gate in the same commit; a gate that outlives the thing it "
        "guards is green forever."
    )
    end = text.find("\n## ", start)
    assert end != -1, "the active-probing offer is no longer inside a section this gate can bound"
    return " ".join(_REFERENCE.sub(" ", text[start:end]).split())


def _cost_paragraph() -> str:
    """The paragraph of that section which states the cost, where the strict rule is affordable."""
    text = DOC.read_text(encoding="utf-8")
    start = text.find("**One operation is")
    assert start != -1, (
        "docs/WHY_GET_VERIFIED.md no longer opens its cost paragraph with `**One operation is`. "
        "That sentence is the offer's statement of what reaches the applicant's server; if it was "
        "reworded, repoint this scope in the same commit."
    )
    end = text.find("\n\n", start)
    assert end != -1, "the cost paragraph is no longer bounded by a blank line"
    return " ".join(_REFERENCE.sub(" ", text[start:end]).split())


PRESENCE = {
    "web/src/pages/Apply.tsx (the option)": _option,
    "docs/WHY_GET_VERIFIED.md (the cost paragraph)": _cost_paragraph,
}
"""The two places the offer is MADE. Both owe a statement of what arrives at the applicant's
server, because silence there is the state this task found."""

PAGE_QUANTITIES = (
    # EVERY QUANTITY THE INTAKE PAGE IS ALLOWED TO STATE beside the prober's own number, each one
    # declared as ENOUGH OF ITS OWN SENTENCE TO IDENTIFY IT. A number that is not covered here is a
    # number nobody has looked at, and on the page where a stranger decides what may touch their
    # production system, a number nobody has looked at is a promise nobody has checked.
    #
    # THE PHRASES ARE THIS LONG BECAUSE SHORT ONES WERE A DOOR. An earlier draft declared the bare
    # keys `one`, `two`, `only one`, `one operation`, `two controls` - the quantity plus at most one
    # following word - and compared new copy against them. Fable then wrote six false promises that
    # needed no new declaration at all, because each one landed on a key already granted: "the
    # number of requests we send is one", "we send two controls and nothing else at your origin",
    # and - on the confirmation screen itself - "in practice what reaches you is only one". Every
    # one of them was green. A declaration must therefore SPAN the number in its own context, and a
    # quantity is permitted only where the declared text encloses it, so reusing a permission means
    # reproducing a whole sentence that cannot be repurposed into a lie about request counts.
    # AND NO LONGER THAN THEY NEED TO BE. The first version of this list quoted whole sentences
    # including the count that follows them - "That one operation costs your origin three requests"
    # - so rewriting the count to "three HTTP requests", which is true and which the green runs in
    # RED-019 require to stay green, broke the declaration and turned the page red for saying the
    # right thing. A declaration spans its own quantity and stops; it may not depend on the wording
    # of a neighbouring one.
    "because nothing here has promised one",   # of a date, not of a request
    "names the one action",                    # the confirmation screen
    "what each one could not measure",         # the registry link
    "the one channel that certainly works",    # the failure notice
    "One operation exists today",              # our unit of account, not what we send
    "That one operation costs your origin",    # the same unit, introducing the real count
    "Without those two controls",              # the positive and negative controls, not a total
    "any later one money does not pass through us",
    "the two-letter country",
    "plus four fields about the record",
    "which one we applied",
    "always the read-only one",
)

SECTION_QUANTITIES = (
    # The same, for the document's offer section. It is held strictly rather than by the weaker
    # noun-based rule it used to have, because that rule could not see a count carried by an adverb
    # - "your server hears from us once" states a number, names no noun, and was green there while
    # the limitation was written down two files away. A disclosed blind spot is still a blind spot
    # (L-25), and stripping decision references is what makes the strict rule affordable here.
    "it is one operation wide",
    "does exactly one thing",
    "enforcing one are different things",
    "run against one subject",
    "**One operation is",
    "it is the one your logs will show",
    "Without those two controls",
    "live system without one is an incident",
    "records that you want one",
    "change the second one",
    "the opposite for one day",
)

STRICT = {
    "web/src/pages/Apply.tsx (the whole page)": (_page, PAGE_QUANTITIES),
    "docs/WHY_GET_VERIFIED.md (the offer section)": (_offer_section, SECTION_QUANTITIES),
}
"""Where every quantity must be declared: both surfaces, whole, with no weaker rule beside them.

THE DOCUMENT USED TO GET THE WEAK RULE and it was the wrong trade. A noun-based check cannot see
"your server hears from us once", so the section carried a hole that was disclosed in a docstring
instead of closed - and the sentence a reader receives is false either way. Running the strict rule
over the section costs the declarations above and nothing else, because `_offer_section` strips the
decision references and status codes that were the only reason the section looked unaffordable."""


def test_the_files_this_gate_guards_still_exist() -> None:
    """A gate pointed at a moved file reports clean forever - L-16's shape."""
    for path in (FORM, DOC):
        assert path.is_file(), (
            f"{path} is missing. If the offer moved, move this gate with it in the same commit "
            "rather than letting it pass over nothing."
        )


def test_the_stripper_removes_the_explanation_and_keeps_the_copy() -> None:
    """INSTRUMENT CONTROL. This gate's own reasoning about three requests is written into
    `Apply.tsx` as a docstring, and the number appears there in prose. A stripper that had stopped
    stripping would find it in the explanation and report the page compliant while the visible copy
    said nothing at all - a gate reading its own justification, which is the failure that looks
    exactly like success."""
    code = _code(FORM)
    assert "T-A2-5" not in code, "the stripper is leaking comments into the code it judges"
    assert "Ask about an active-probing mandate" in code, "the stripper has eaten the copy as well"
    assert _quantities(_page()), (
        "no quantity at all was found on the intake page, which no version of this copy has ever "
        "been true of. The extractor has eaten the page rather than cleaned it, and every "
        "assertion below would pass over an empty string"
    )


def test_the_extractor_keeps_the_copy_that_is_conditionally_rendered() -> None:
    """THE SECOND INSTRUMENT CONTROL, and it is here because the extractor failed exactly this way.

    Everything this page says AFTER a submission - the confirmation, the failure notice, the
    delivered/not-delivered branch - lives inside a `{...}` expression, and the first version of
    `_page()` stripped `\\{[^{}]*\\}`, which is all of them. The scan then ran over a page with no
    confirmation screen on it: the surface Fable had just found unguarded, silently dropped by the
    very widening that was supposed to cover it. A count could have been moved into any of those
    branches and said anything at all.

    Asserting on the quantity list alone would not have caught it - the page still had ten
    quantities without them. What catches it is naming a sentence from each branch.
    """
    page = _page()
    for branch, sentence in {
        "the confirmation shown to an active-mandate applicant":
            "You asked about an active-probing mandate",
        "the confirmation shown to every applicant": "Your request is recorded",
        "the failure notice": "Not recorded",
        "the option itself": "One operation exists today",
    }.items():
        assert sentence in page, (
            f"{branch} did not survive extraction: `{sentence}` is in web/src/pages/Apply.tsx and "
            "is not in what this gate reads. Copy the gate cannot see is copy the gate does not "
            "hold, and a visitor reads it either way."
        )


def test_the_extractor_keeps_a_sentence_containing_an_apostrophe() -> None:
    """THE THIRD INSTRUMENT CONTROL, and it is separate from the one above because the one above
    could not have caught what it is for.

    `_STRING` used to strip `'...'` as well as `"..."`. Prose does not know it is inside a program:
    "we don't send more than one request, and we won't retry" has two apostrophes, so everything
    between them was deleted and the count inside it went with them. Every sentence the control
    above names happens to have no apostrophe, which is why four assertions passed over it.

    Rather than name a sentence that may be rewritten, this feeds the extractor prose of its own -
    a red here means the stripper has started eating copy again, whatever the page currently says.
    """
    sample = "<p>We don't send more than one request, and we won't retry.</p>"
    assert "one request" in _visible(sample), (
        "the extractor is deleting prose between two apostrophes. A promise a visitor reads would "
        "be invisible to every assertion in this file, which is the failure that looks exactly "
        "like a clean page."
    )


def test_the_extractor_keeps_copy_that_reaches_the_page_through_a_constant() -> None:
    """THE FOURTH INSTRUMENT CONTROL, for the third time this extractor dropped copy silently.

    A sentence can be a string literal AND what a visitor reads - `ISSUES` and `DECISION_LOG` on
    this page are already written that way, so it is the ordinary way to add one:

        const REASSURANCE = "In practice only one request ever reaches your server.";
        <p className="mt-4 text-sm">{REASSURANCE}</p>

    While every `"..."` was stripped as configuration, that sentence was invisible to all ten
    assertions and the suite was green over a promise of one request. Removals are by ROLE now -
    technical attributes and addresses - and this control is what stops "strings are code" coming
    back as a simplification.

    Like the apostrophe control, it feeds the extractor prose of its own rather than naming a
    sentence on the page, so no rewrite of the copy can quietly disarm it.
    """
    sample = ('const REASSURANCE = "In practice only one request ever reaches your server.";\n'
              '<p className="mt-4 text-sm">{REASSURANCE}</p>')
    cleaned = _visible(sample)
    assert "only one request" in cleaned, (
        "copy defined as a string constant and rendered through an expression does not survive "
        "extraction. A visitor reads it; this gate does not; and the numbers in it are checked by "
        "nothing at all."
    )
    assert "mt-4" not in cleaned, (
        "the class name survived, so the extractor is reading attributes as copy and every styling "
        "numeral is about to be reported as a promise"
    )


def test_the_markup_scan_finds_every_screen_this_page_can_render() -> None:
    """INSTRUMENT CONTROL for the block matcher, which decides where copy is looked for at all.

    `_jsx_blocks` walks parentheses. A matcher that returned one block instead of two - the early
    return for the confirmation screen is a separate `return (` from the form's - would silently
    drop a whole screen, which is the failure this extractor has already committed three times in
    other forms. Counting blocks is not enough on its own, so a sentence from each is named too.
    """
    blocks = _jsx_blocks(_code(FORM))
    assert len(blocks) >= 2, (
        f"the intake page yields {len(blocks)} markup blocks; this gate was written against at "
        "least two - the confirmation screen and the form. A matcher that collapses them drops a "
        "whole screen's copy, and a screen whose copy nobody checks is where every promise this "
        "gate exists for would go."
    )
    joined = " ".join(blocks)
    for sentence in ("You asked about an active-probing mandate", "One operation exists today"):
        assert sentence in joined, (
            f"`{sentence}` is on the page and outside every block this gate reads. Copy the gate "
            "cannot see is copy the gate does not hold."
        )


def test_a_tooltip_cannot_satisfy_the_requirement_to_state_the_cost() -> None:
    """THE FIFTH CONTROL, and it holds a distinction rather than an extraction.

    `title` is read by somebody hovering a mouse - not on touch, not from a keyboard, not by
    anyone who simply reads the page. When the extractor kept it as copy, this passed:

        <span title="three requests">That one operation costs your origin very little.</span>

    The offer stated in our unit and softened to "very little", with the real cost reachable only
    by hovering, on a suite that was green in all eleven assertions. A readable attribute may not
    CONTRADICT the count - `_page` gathers it for exactly that - but it may not be how the page
    COMPLIES either, and those two rules pull in opposite directions, so both are asserted here.
    """
    tooltip = '<span title="three requests">costs your origin very little.</span>'
    assert not _states_the_count(_visible(tooltip)), (
        "a count in a `title` attribute satisfies the presence rule. The offer can then be softened "
        "to 'very little' on the screen where a stranger decides, with the number reachable only "
        "by hovering a mouse - which is the defect T-A2-5 was opened to remove."
    )
    quantities = _quantities(" ".join(m.group(1) for m in _COPY_ATTRIBUTE.finditer(tooltip)))
    assert quantities, (
        "readable attributes are no longer gathered at all, so a tooltip contradicting the count - "
        "`title=\"ninety requests\"` - would be invisible to the strict rule. Not usable to comply "
        "is one rule; not usable to contradict is the other, and this half has gone"
    )


def test_the_pages_own_javascript_is_not_read_as_a_promise() -> None:
    """THE SIXTH CONTROL, and it guards the FALSE-RED direction, which is how a gate gets deleted.

    An earlier draft read the whole module, so a maintainer adding an ordinary rate-limit branch
    met a red telling them their status code was "neither the 3 requests src/prober/prober.py
    spends nor a quantity this gate has been told about" and inviting them to consider whether it
    was a promise we do not keep about somebody's production server. It was a status code. L-5:
    a gate that cries over correct work teaches walking past it exactly as a false green does, and
    this one would have fired on the next unrelated edit to `Apply.tsx`.
    """
    code = ('async function submit(e: React.FormEvent<HTMLFormElement>) {\n'
            '  if (r.status === 429) { return; }\n'
            '  for (let i = 0; i < 3; i++) { await go(); }\n'
            '  const RETRY_AFTER_MS = 3000;\n'
            '  const message = `retry in 30 seconds`;\n'
            '}\n'
            'return (<p className="mt-4 text-sm">Nothing is charged.</p>);')
    visible = _visible(code)
    assert _quantities(visible) == {}, (
        f"the page's own JavaScript is reaching the quantity rules as {_quantities(visible)}. A "
        "status code, a loop bound, a timeout constant and a template literal are not promises to "
        "an applicant, and reporting them as second counts is the red that gets this gate switched "
        "off. Worse, it was POSITION-DEPENDENT: the same status guard passed above one brace pair "
        "and failed below the next, so an editor could not even form a rule from it."
    )
    assert "Nothing is charged." in visible, (
        "the extractor dropped the visible sentence while dropping the code, so this control is "
        "passing over an empty string rather than over a page with no numerals in its JavaScript"
    )


@pytest.mark.parametrize("surface", sorted(PRESENCE))
def test_the_offer_states_how_many_requests_reach_the_applicant(surface: str) -> None:
    """The state this task found: an offer stated only in operations."""
    assert _states_the_count(PRESENCE[surface]()), (
        f"the active-probing offer in {surface} does not say how many requests one probe sends to "
        f"the applicant's origin. src/prober/prober.py spends {CALLS_PER_PROBE} of them - a "
        "positive control, a negative control and the attempt - and 'one operation' is our unit of "
        "account, not the unit that arrives at their server. The person reading this offer is "
        "deciding what may touch their live system; an offer narrower than the artefact behind it "
        "is the defect this project exists to find, and worse when the artefact is ours."
    )


@pytest.mark.parametrize("surface", sorted(STRICT))
def test_every_quantity_stated_is_the_probers_or_a_declared_one(surface: str) -> None:
    """The rule that does not depend on guessing which nouns a softening sentence will use.

    A second count - "in practice it is usually a single call", "your server hears from us once",
    "the ninety HTTP requests it spends" - is caught here whatever noun it hangs on, because what
    is checked is the number. Five sentences of exactly that shape passed earlier drafts of this
    file, and each of them was a promise about somebody's production system.
    """
    scope, permitted = STRICT[surface]
    stray = _undeclared(scope(), permitted)
    assert not stray, (
        f"{surface} states {stray}, which is neither the {CALLS_PER_PROBE} requests "
        "src/prober/prober.py spends nor a quantity this gate has been told about. If it is a "
        "second count of what reaches the applicant's server, it is a promise we do not keep - "
        "and if it counts something else entirely, add the phrase to this gate so that the next "
        "number appearing here is still a red. A number nobody looked at, on the page where a "
        "stranger decides what may touch their production system, is the defect this project "
        "exists to find."
    )


@pytest.mark.parametrize("surface", sorted(STRICT))
def test_every_declared_quantity_is_still_on_the_page(surface: str) -> None:
    """A declaration whose sentence has gone is a permission nobody revoked.

    The list above is the only place this gate can be widened, so it is the only place it can rot.
    A phrase left behind after its copy was rewritten grants a number that no longer has a reason,
    and the next editor to write that number would find the gate already agreeing with them -
    L-16's shape, inside the allowlist rather than in a path.
    """
    scope, permitted = STRICT[surface]
    text = scope()
    missing = sorted(p for p in permitted if p not in text)
    assert not missing, (
        f"{surface} no longer contains {missing}, which this gate still permits a quantity for. "
        "Either the copy was rewritten and the declaration should go with it, or the declaration "
        "was mistyped and has been permitting nothing since it was added - and a permission for a "
        "sentence that is not there is one an editor will meet as agreement."
    )
