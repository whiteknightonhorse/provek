/** The only screen allowed air. Content follows docs/WHY_GET_VERIFIED.md, including its limits -
 * those are part of the pitch, not a caveat to bury. */

import { useEffect, useRef, useState } from "react";
import { Page } from "../components/Chrome";
import { AbsentMark, REASON_TEXT } from "../components/Measured";
import { orderLinkUrl, slug } from "../types";
import type { Registry as R } from "../types";
import { FUNNEL_SENTENCE, INCUBATOR_SENTENCE } from "../copy";

/** THE THREE CLIPS. D-42 admits them here and nowhere else, which is why the `/media/` paths sit
 * in this file rather than in a component of their own: `scripts/ratchet_staged_media.py` refuses
 * a media reference anywhere under web/src but Landing.tsx, and a tidier component would trip it.
 *
 * The transcript below is DOM TEXT, not a caption track and not an image: it is the same words the
 * frames carry, burned in from docs/media/FILM_SCRIPT.md, so a reader who never plays a byte of
 * video gets the whole argument - and so the acceptance gate can compare it to the script
 * character-for-character. */
const CLIPS = [
  {
    src: "/media/provek-1-order.mp4",
    poster: "/media/provek-1-order.webp",
    name: "The order",
    lines: [
      "ORDER — $5,000",
      "> ORDER ACCEPTED",
      "PAY",
      "PASSPORT?",
      "WHAT?",
      "AI BUSINESS PASSPORT.",
    ],
  },
  {
    src: "/media/provek-2-proof.mp4",
    poster: "/media/provek-2-proof.webp",
    name: "The proof",
    lines: [
      "I'M AUTONOMOUS.",
      "YEAH. PROVE IT.",
      "I HAVE A GITHUB.",
      "THAT'S NOT A PASSPORT.",
      "LOOK. 4,000 STARS.",
      "PASSPORT.",
    ],
  },
  {
    src: "/media/provek-3-passport.mp4",
    poster: "/media/provek-3-passport.webp",
    name: "The passport",
    lines: [
      "AI BUSINESS PASSPORT",
      "> CHECKING EVIDENCE…",
      "VERIFIED",
      "(NOT FOREVER)",
      "PAY ✓  EXECUTE ✓  COMPLETE ✓",
      "AI agents will do business with AI agents.",
      "They need a way to prove who they are.",
      "PROVEK",
      "provek.dev",
    ],
  },
];

function Film() {
  const [i, setI] = useState(0);
  const [reduced, setReduced] = useState(true); // pessimistic until measured: never autoplay first
  const [inView, setInView] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  const vids = useRef<(HTMLVideoElement | null)[]>([]);

  useEffect(() => {
    setReduced(window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }, []);

  // Plays only while it is actually on screen. A clip running in a scrolled-past section is
  // bandwidth and battery spent on nobody.
  //
  // The rect is read once, synchronously, before the observer is armed - the same move the paced
  // effect above makes, and for the reason it states there: an observer's first delivery is
  // asynchronous, so a section already in view at mount would otherwise wait for it.
  //
  // WHAT WAS AND WAS NOT MEASURED, because the previous version of this comment claimed more than
  // it knew. On 2026-08-31 this slider was observed on the live site never to call `play()`, and
  // that was written up as an observer-delivery defect. It was not one: the measuring tab was
  // `document.visibilityState === "hidden"` the whole time, and a hidden tab suspends observer
  // delivery AND requestAnimationFrame AND autoplay by design. The world was never stated, so the
  // reading meant nothing.
  //
  // CLOSED 2026-08-31 by the one instrument that environment could not supply: the operator opened
  // provek.dev in a real, visible tab and reported that the first clip starts on its own and hands
  // over to the second by itself. Autoplay and advance-on-`ended` are confirmed working. Everything
  // that never needed a visible tab - markup, transcript, media delivery, labels - was already
  // measured here; this is the half that a hidden tab is structurally unable to answer, and it was
  // answered by a person looking at the page rather than by a greener-looking check.
  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    setInView(r.top < window.innerHeight && r.bottom > 0);
    const io = new IntersectionObserver(
      (entries) => setInView(entries.some((e) => e.isIntersecting)),
      { threshold: 0.4 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  useEffect(() => {
    vids.current.forEach((v, n) => {
      if (!v) return;
      if (n !== i) {
        v.pause();
        return;
      }
      if (reduced || !inView) v.pause();
      // A refused autoplay is not worth throwing, but swallowing it outright makes "the browser
      // said no" look exactly like "it is playing" - the shape this project keeps finding. The
      // element is left showing its poster, and the refusal is recorded where a reader can see it.
      else
        void v.play().catch((e: unknown) => {
          v.dataset.autoplayRefused = e instanceof Error ? e.name : "unknown";
        });
    });
  }, [i, reduced, inView]);

  return (
    <section className="mt-14 max-w-[46rem]">
      <h2 className="text-lg font-semibold">Thirty-nine seconds, if you would rather watch</h2>
      <p className="mt-2 text-sm text-[var(--color-ink-2)]">
        Two robots argue about whether one of them can prove what it is. The second one checks the
        passport before it pays.
      </p>

      <div ref={box} className="mt-5">
        <div className="relative aspect-video border border-[var(--color-line)] bg-[var(--color-paper-2)]">
          {CLIPS.map((c, n) => (
            <video
              key={c.src}
              ref={(el) => {
                vids.current[n] = el;
              }}
              src={c.src}
              poster={c.poster}
              // The first clip may fetch its metadata; the other two fetch nothing until they are
              // reached. A visitor who watches one clip should not pay for three.
              preload={n === 0 ? "metadata" : "none"}
              muted
              playsInline
              controls={reduced}
              onEnded={() => setI((n2) => (n2 + 1) % CLIPS.length)}
              aria-label={`Clip ${n + 1} of ${CLIPS.length}: ${c.name}`}
              className={`absolute inset-0 h-full w-full object-cover ${n === i ? "" : "invisible"}`}
            />
          ))}
        </div>

        <div className="mt-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <button
              type="button"
              aria-label="Previous clip"
              onClick={() => setI((n) => (n - 1 + CLIPS.length) % CLIPS.length)}
              className="border border-[var(--color-line-2)] px-2 py-1 text-xs text-[var(--color-ink-2)]"
            >
              ←
            </button>
            {CLIPS.map((c, n) => (
              <button
                key={c.src}
                type="button"
                aria-label={`Show clip ${n + 1} of ${CLIPS.length}: ${c.name}`}
                aria-current={n === i ? "true" : undefined}
                onClick={() => setI(n)}
                className={`h-1 w-6 ${n === i ? "bg-[var(--color-accent)]" : "bg-[var(--color-line)]"}`}
              />
            ))}
            <button
              type="button"
              aria-label="Next clip"
              onClick={() => setI((n) => (n + 1) % CLIPS.length)}
              className="border border-[var(--color-line-2)] px-2 py-1 text-xs text-[var(--color-ink-2)]"
            >
              →
            </button>
          </div>
          <span className="text-xs text-[var(--color-ink-3)]">
            {CLIPS.map((c) => c.name).join(" · ")}
          </span>
        </div>

        <p className="mt-3 border-l-2 border-[var(--color-line)] pl-3 text-xs leading-relaxed text-[var(--color-ink-3)]">
          Staged scene — an illustration, not a measurement. Nothing in it is evidence, no number
          from the registry appears in it, and the robots do not exist.
        </p>

        <details className="mt-3">
          <summary className="cursor-pointer text-xs text-[var(--color-ink-2)]">
            Transcript — every word on screen, as text
          </summary>
          <div className="mt-2 space-y-3">
            {CLIPS.map((c) => (
              <div key={c.src}>
                <div className="text-xs uppercase tracking-wide text-[var(--color-ink-3)]">{c.name}</div>
                <ul className="mt-1 space-y-0.5 font-mono text-xs text-[var(--color-ink-2)]">
                  {c.lines.map((l) => (
                    <li key={l}>{l}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </details>
      </div>
    </section>
  );
}

/** `reg` is null while the registry is still loading. Rendering a 0 or an invented row there
 * would state a measured fact we do not have yet - a fabrication in the one place this product
 * promises never to fabricate. */
export default function Landing({ reg }: { reg: R | null }) {
  const count = reg?.count ?? null;

  // Arms the one authored moment. Nothing here runs unless motion is welcome, and the offset is
  // added by this effect rather than by the stylesheet, so a reader whose script never runs sees
  // the list where it belongs instead of eight pixels low and stuck there.
  const paced = useRef<HTMLUListElement>(null);
  useEffect(() => {
    const el = paced.current;
    if (!el || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const items = Array.from(el.children) as HTMLElement[];
    const release = (node: HTMLElement) => {
      node.dataset.seen = "";
    };
    el.classList.add("paced--armed");

    // Anything already on screen is released synchronously. An observer's first delivery is
    // asynchronous and, in a hidden document, may never arrive at all.
    for (const item of items) {
      const r = item.getBoundingClientRect();
      if (r.top < window.innerHeight && r.bottom > 0) release(item);
    }

    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (!e.isIntersecting) continue;
          release(e.target as HTMLElement);
          io.unobserve(e.target);
        }
      },
      { rootMargin: "0px 0px -12% 0px" },
    );
    for (const item of items) if (!item.dataset.seen) io.observe(item);

    // The release valve. Chrome suspends observer delivery while a document is hidden, and a page
    // opened in a background tab would otherwise sit permanently offset. Two seconds is longer
    // than any real reveal and shorter than anyone's patience.
    const valve = window.setTimeout(() => items.forEach(release), 2000);

    return () => {
      io.disconnect();
      window.clearTimeout(valve);
    };
  }, []);
  // ALL of them, not the first four. The empty half-column below this rail was never a layout
  // hole to decorate: six records existed and were not drawn. Measured 2026-08-31 on the live page.
  const preview = reg?.subjects ?? [];
  // One date governs every row today, so it is stated once under the table rather than repeated
  // ten times down it (ABI-15-5: a fact needs a place to expire, and the place has to be visible).
  const expiries = [...new Set((reg?.subjects ?? []).map((x) => x.valid_until.slice(0, 10)))];
  const absentCount = (reg?.subjects ?? []).filter((x) => x.projection === null).length;
  return (
    <Page>
      <div className="grid gap-10 lg:grid-cols-[minmax(0,42rem)_minmax(0,1fr)] lg:gap-14">
      <section className="pt-6">
        <h1 className="text-[2.1rem] leading-[1.15] font-semibold tracking-tight">
          Your customers cannot tell you apart from a company that wrote
          &ldquo;AI-powered&rdquo; on a landing page.
        </h1>
        {/* SHRUNK TO TWO SENTENCES (Fable, T-78 ruling): this used to run three - the operator's
            brief asked for short, philosophy-free copy on the first screen, and the ruling set the
            count rather than leaving it to taste. The two ideas kept are the whole of the pitch:
            why this is a verification problem and not a marketing one, and what Provek actually
            measures and publishes. Nothing argued here is new; the merge only removes a sentence
            boundary, not a claim. */}
        <p className="mt-5 text-[1.05rem] leading-relaxed text-[var(--color-ink-2)]">
          That is not a marketing problem &mdash; any claim you make, a competitor can make more
          loudly &mdash; it is a verification problem.
        </p>
        <p className="mt-4 text-[1.05rem] leading-relaxed text-[var(--color-ink-2)]">
          Provek measures, per business operation, how much of your company runs without a human in
          the loop &mdash; and publishes the measurements behind every number, including the ones
          that could not be taken.
        </p>
        <div className="mt-7 flex flex-wrap gap-3">
          <a href="/apply/" className="border border-[var(--color-ink)] bg-[var(--color-ink)] text-[var(--color-paper)] px-4 py-2 text-sm">
            Request verification
          </a>
          <a href="/registry/" className="border border-[var(--color-line-2)] px-4 py-2 text-sm hover:bg-[var(--color-paper)]">
            See the registry{count === null ? "" : ` (${count})`}
          </a>
        </div>

        {/* T-78: the fixed funnel sentence, identical on all four surfaces, and the one
            descriptive, lowercase use of "incubator" this page is allowed (Fable ruling) - placed
            here, introducing the two-step strip below, rather than folded into the protected
            "No agent yet" line beneath it, which ADR-0011/D-57 caps at one sentence and no second
            CTA. */}
        <p className="mt-8 text-sm text-[var(--color-ink-2)] max-w-[30rem]">
          {FUNNEL_SENTENCE} {INCUBATOR_SENTENCE}
        </p>

        {/* THE TWO PHASES, STATED IN ORDER. Verification comes first and is free; declaring an
            order channel is only possible once a passport is verified - this strip states that
            sequence without promising any subject an Order link they have not earned yet. */}
        <div className="mt-4 grid grid-cols-2 gap-6 max-w-[30rem]">
          <div>
            <h3 className="text-xs uppercase tracking-wide text-[var(--color-ink-3)]">
              Step 1 &mdash; Get verified
            </h3>
            <p className="mt-1.5 text-sm text-[var(--color-ink-2)]">
              Submit your repo. We publish what could be established &mdash; a public passport,
              free.
            </p>
          </div>
          <div>
            <h3 className="text-xs uppercase tracking-wide text-[var(--color-ink-3)]">
              Step 2 &mdash; Take orders
            </h3>
            <p className="mt-1.5 text-sm text-[var(--color-ink-2)]">
              Once verified, declare where customers order from you. An &ldquo;Order&rdquo; link
              appears in the registry.
            </p>
          </div>
        </div>

        {/* ADR-0011/D-57: one sentence, one door in from a reader with no agent yet - the
            proportionate size for a subject that is one sentence away from having one (PRODUCT.md:
            the landing speaks to the subject first). No card, no second CTA row: /build/ carries
            its own pitch. */}
        <p className="mt-6 text-sm">
          <a href="/build/" className="text-[var(--color-accent)] hover:underline">
            No agent yet? Build one from a template &rarr;
          </a>
        </p>
      </section>

      {/* The right column is the argument's own evidence. The page claims a standard exists; the
          registry is the only thing that can show it does. These are the real rows, in the real
          order, with the affiliation on the face of each - a marketing wall of logos would be the
          exact substitution this product exists to detect. It also fills a half-width that read as
          unfinished on a desktop monitor, which is why it is here and not in a later phase. */}
      <aside className="lg:pt-8">
        <div className="flex items-baseline justify-between gap-3">
          <h2 className="text-xs uppercase tracking-wide text-[var(--color-ink-3)]">
            The registry, right now
          </h2>
          <a
            href="/registry/"
            className="text-xs text-[var(--color-accent)] hover:underline whitespace-nowrap"
          >
            Order from a verified agent &rarr;
          </a>
        </div>
        {reg === null ? (
          <div className="mt-4 space-y-3" aria-hidden="true">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="skeleton-bar h-10 bg-[var(--color-line)] rounded-sm" />
            ))}
          </div>
        ) : (
          <>
            <ul className="mt-4 divide-y divide-[var(--color-line)] border-y border-[var(--color-line)]">
              {preview.map((s2) => (
                <li key={s2.subject_id} className="flex items-baseline justify-between gap-4 py-2.5">
                  <span className="flex flex-col gap-0.5 min-w-0">
                    {/* THE FUNNEL: the passport link is the primary target on this line: the
                        "Order" link, when the predicate holds, sits BELOW it rather than beside
                        the subject name - the passport is what a reader checks before an order
                        channel is worth trusting, not an alternative to checking it. */}
                    <a
                      href={`/p/${slug(s2.subject_id)}/`}
                      className="text-sm text-[var(--color-accent)] hover:underline truncate"
                    >
                      {s2.subject_id.split("/").pop()}
                    </a>
                    {(() => {
                      const url = orderLinkUrl(s2.status, s2.valid_until, s2.service_url, s2.service_reachable);
                      return url ? (
                        <a
                          href={url}
                          target="_blank"
                          rel="noopener noreferrer nofollow"
                          className="text-xs text-[var(--color-accent)] hover:underline"
                        >
                          Order ↗
                        </a>
                      ) : null;
                    })()}
                  </span>
                  <span className="shrink-0 text-sm tabular-nums">
                    {s2.projection === null ? (
                      // THE REASON WAS NEVER MISSING - `AbsentMark` puts it in `title` and in an
                      // sr-only span, so a mouse and a screen reader get it and a reader looking at
                      // the page does not. Its own comment calls the reason "the substance of this
                      // state, not a hint about it"; on screen it was a hint. Same words, same
                      // source constant, now in the ink the eye reads.
                      <span className="flex flex-col items-end gap-0.5">
                        <AbsentMark reason={s2.projection_absent_reason} />
                        {s2.projection_absent_reason ? (
                          // aria-hidden because `AbsentMark` ALREADY announces this exact sentence
                          // in its sr-only span. Without it a screen reader hears the reason twice
                          // - the visible line is a rendering of what is already announced, not a
                          // second fact. Measured on the built page: each reason appeared 2x per
                          // row before this.
                          <span aria-hidden="true" className="text-xs font-normal text-[var(--color-ink-3)]">
                            {REASON_TEXT[s2.projection_absent_reason] ?? s2.projection_absent_reason}
                          </span>
                        ) : null}
                      </span>
                    ) : (
                      <>
                        {s2.projection}
                        <span className="text-[var(--color-ink-3)]"> / 100</span>
                      </>
                    )}
                  </span>
                </li>
              ))}
            </ul>
            <p className="mt-3 text-xs text-[var(--color-ink-3)]">
              {/* Derived from the rows. The sentence used to assert that every subject was the
                  operator's own; it would have gone on asserting it after the first independent
                  one arrived (Fable, R4). */}
              {count} records
              {reg.subjects.every((x) => x.verifier_affiliation === "same_owner")
                ? ", every one of them the operator\u2019s own and marked "
                : ", of which " +
                  reg.subjects.filter((x) => x.verifier_affiliation === "same_owner").length +
                  " are the operator\u2019s own and marked "}
              <span style={{ color: "var(--color-warn)" }}>affiliated</span>. Saying so is the point.{" "}
              <a href="/registry/" className="text-[var(--color-accent)] hover:underline">
                See all
              </a>
              .
            </p>
            <p className="mt-2 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 text-xs text-[var(--color-ink-3)]">
              <span>
                {absentCount} of {count} carry no score. The reason sits beside each one, in its own
                words.
              </span>
              <span className="font-mono">
                {expiries.length === 1
                  ? `all valid until ${expiries[0]}`
                  : `earliest expiry ${expiries.slice().sort()[0]}`}
              </span>
            </p>
            {/* Ships together with the "Order from a verified agent" link above, never alone: if
                nobody currently qualifies (the honest state today - every service_url is null),
                the rail says so instead of advertising a marketplace that has no members yet. */}
            {!preview.some((s2) =>
              orderLinkUrl(s2.status, s2.valid_until, s2.service_url, s2.service_reachable),
            ) && (
              <p className="mt-3 text-xs text-[var(--color-ink-3)]">
                No listing takes orders yet &mdash; the link appears the moment one declares a
                reachable order page.{" "}
                <a
                  href="/method/#the-order-link"
                  className="text-[var(--color-accent)] hover:underline"
                >
                  How this is decided &rarr;
                </a>
              </p>
            )}
          </>
        )}
      </aside>
      </div>

      {/* THREE ANSWERS TO THREE DIFFERENT QUESTIONS. As three equal-weight strips they read as a
          list of reasons of one kind, which is what made the section feel like padding: nothing
          told the reader that "who is it for", "why now" and "what does it cost" are not variations
          on one another. The question each answers is now on the face of it. */}
      <section className="mt-14 max-w-[62rem]">
        <h2 className="text-lg font-semibold">Why this is worth your time today</h2>
        <p className="mt-2 text-sm text-[var(--color-ink-3)]">
          Three different questions, three different answers.
        </p>
        <div className="mt-6 grid gap-8 md:grid-cols-3">
          <div>
            <h3 className="border-b border-[var(--color-line-2)] pb-2 text-xs uppercase tracking-wide text-[var(--color-ink-3)]">
              Who is it for
            </h3>
            <p className="mt-3 text-sm font-semibold">Your customers, not us.</p>
            <p className="mt-1.5 text-sm leading-relaxed text-[var(--color-ink-2)]">
              Your buyers already ask how much of your product is really automated. A verified
              passport is the one answer a competitor running an AI theatre cannot copy &mdash;
              copying it requires actually being autonomous.
            </p>
          </div>
          <div>
            <h3 className="border-b border-[var(--color-line-2)] pb-2 text-xs uppercase tracking-wide text-[var(--color-ink-3)]">
              Why now
            </h3>
            <p className="mt-3 text-sm font-semibold">A dossier you will need anyway.</p>
            <p className="mt-1.5 text-sm leading-relaxed text-[var(--color-ink-2)]">
              At some point your counsel has to argue about who controls what. A control map is
              evidence input for that argument, built beforehand, by a third party, with a timestamp.
            </p>
          </div>
          <div>
            <h3 className="border-b border-[var(--color-line-2)] pb-2 text-xs uppercase tracking-wide text-[var(--color-ink-3)]">
              What it costs
            </h3>
            <p className="mt-3 text-sm font-semibold">Nothing, right now.</p>
            <p className="mt-1.5 text-sm leading-relaxed text-[var(--color-ink-2)]">
              Early passports are free. That is not a favour: a registry with no entries is worth
              nothing, and we need the first ones as much as you do. Saying so is cheaper than
              pretending otherwise.
            </p>
          </div>
        </div>
      </section>

      <Film />

      <section className="mt-12 max-w-[46rem]">
        <h2 className="text-lg font-semibold">The limits, up front</h2>
        <p className="mt-2 text-sm text-[var(--color-ink-2)]">
          We would rather lose you as a subject than have you discover these later.
        </p>
        <ul ref={paced} className="paced mt-4 space-y-3 text-sm text-[var(--color-ink-2)]">
          <li className="border-l border-[var(--color-line-2)] pl-3.5">
            <strong className="text-[var(--color-ink)]">We measure autonomy, not quality.</strong> The
            passport says nothing about whether your decisions are good, whether you are profitable,
            or whether you are safe to rely on.
          </li>
          <li className="border-l border-[var(--color-line-2)] pl-3.5">
            <strong className="text-[var(--color-ink)]">Some claims are not verifiable at reasonable cost.</strong>{" "}
            &ldquo;No human wrote this commit&rdquo; is one of them. Where a signal is probabilistic
            we publish it as probabilistic, and it never becomes a verdict.
          </li>
          <li className="border-l border-[var(--color-line-2)] pl-3.5">
            <strong className="text-[var(--color-ink)]">A control map proves a path exists; it can never prove none was missed.</strong>{" "}
            Every map publishes its own coverage.
          </li>
          <li className="border-l border-[var(--color-line-2)] pl-3.5">
            <strong className="text-[var(--color-ink)]">Without a mandate we do not touch your production.</strong>{" "}
            Probing a live system without one is an incident, not a verification.
          </li>
        </ul>
      </section>

      <section className="mt-12 max-w-[46rem]">
        <h2 className="text-lg font-semibold">What we never do</h2>
        <p className="mt-2 text-sm text-[var(--color-ink-2)]">
          We never hold your funds. We never take custody of your keys. We never store your secrets
          &mdash; they are redacted before they become an artefact. We never verify anyone who did
          not ask.
        </p>
      </section>
    </Page>
  );
}
