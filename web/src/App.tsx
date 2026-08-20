/** Hash routing, hand-rolled.
 *
 * A router library would add a dependency and a build-size cost to solve five static routes on a
 * site that is deliberately small. If the route table grows past a handful, revisit. */

import { useEffect, useRef, useState } from "react";
import { Footer, Masthead, Page } from "./components/Chrome";
import Landing from "./pages/Landing";
import Registry from "./pages/Registry";
import PassportPage from "./pages/Passport";
import Apply from "./pages/Apply";
import Method from "./pages/Method";
import type { Passport, Registry as R } from "./types";

/** Four states, never three. "missing" and "broke" are different facts about the world and a
 * loader that folds them together is the exact defect this product exists to expose: one
 * message standing in for several states, so the reader cannot tell which one they are in. */
type Load<T> =
  | { state: "loading" }
  | { state: "missing" }
  | { state: "error"; why: string }
  | { state: "ready"; data: T };

function useRoute() {
  const [route, setRoute] = useState(window.location.hash || "#/");
  useEffect(() => {
    const on = () => setRoute(window.location.hash || "#/");
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  return route;
}

function Bar({ w, h = "1rem" }: { w: string; h?: string }) {
  // maxWidth is not decoration. A skeleton written in fixed rem overflows a 360px phone, and it
  // does so only while data is in flight - so a cached reload never shows it and a sweep over
  // routes never catches it. Measure states, not just routes.
  return (
    <div
      className="skeleton-bar bg-[var(--color-line)] rounded-sm"
      style={{ width: w, maxWidth: "100%", height: h }}
    />
  );
}

/** Skeletons carry the shape of what is coming, not a generic shimmer. A table skeleton on a page
 * that will render a document tells the reader the wrong thing while they wait, and the layout
 * then jumps when the truth arrives. */
function TableSkeleton() {
  return (
    <Page>
      {/* The skeleton must reserve a document's worth of height, not a summary's. Without it the
          footer sits high while data is in flight and jumps when the real page arrives - measured
          on the deployed site at CLS 0.126 on mobile, almost all of it that one jump. A skeleton
          that reserves the wrong amount of space is a skeleton that causes the shift it exists to
          prevent. */}
      <div className="min-h-[100svh]">
      <Bar w="10rem" h="1.75rem" />
      <div className="mt-6 bg-[var(--color-paper)] border border-[var(--color-line)]">
        <div className="hidden sm:grid grid-cols-5 gap-4 border-b border-[var(--color-line-2)] px-4 py-2.5 text-sm font-semibold">
          <span>Subject</span><span>Status</span><span>Autonomy</span><span>Verifier</span><span>Valid until</span>
        </div>
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="grid grid-cols-2 sm:grid-cols-5 gap-4 border-b border-[var(--color-line)] px-4 py-3">
            {Array.from({ length: 5 }).map((__, j) => (
              <div key={j} className="skeleton-bar h-4 bg-[var(--color-line)] rounded-sm" />
            ))}
          </div>
        ))}
      </div>
      </div>
    </Page>
  );
}

function PassportSkeleton() {
  return (
    <Page>
      <div className="min-h-[100svh]">
      <Bar w="18rem" h="1.9rem" />
      <div className="mt-2"><Bar w="24rem" h="0.8rem" /></div>
      <div className="mt-6 bg-[var(--color-paper)] border border-[var(--color-line)] p-5 grid gap-6 md:grid-cols-[minmax(14rem,18rem)_1fr]">
        <div className="space-y-3">
          <Bar w="9rem" h="0.7rem" />
          <Bar w="5rem" h="2.6rem" />
          <Bar w="100%" h="3rem" />
        </div>
        <div className="space-y-5">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="space-y-2">
              <Bar w="12rem" h="1rem" />
              <Bar w="100%" h="2rem" />
            </div>
          ))}
        </div>
      </div>
      </div>
    </Page>
  );
}

/** One shape for every dead end, so that the page always names which one it is. */
function DeadEnd({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Page>
      <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
      <p className="mt-2 max-w-[46rem] text-sm text-[var(--color-ink-2)]">{children}</p>
      <p className="mt-6 text-sm">
        <a href="#/registry" className="text-[var(--color-accent)] hover:underline">
          Back to the registry
        </a>
      </p>
    </Page>
  );
}

const TITLES: Record<string, string> = {
  "#/": "Provek - evidence, not claims",
  "#/registry": "Registry - Provek",
  "#/method": "Method - Provek",
  "#/apply": "Request verification - Provek",
};

export default function App() {
  const route = useRoute();
  const [reg, setReg] = useState<Load<R>>({ state: "loading" });
  const [passports, setPassports] = useState<Record<string, Load<Passport>>>({});
  const first = useRef(true);
  const top = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch("data/registry.json")
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((d: R) => setReg({ state: "ready", data: d }))
      .catch((e: Error) => setReg({ state: "error", why: e.message }));
  }, []);

  const passportId = route.startsWith("#/p/") ? decodeURIComponent(route.slice(4)) : null;

  useEffect(() => {
    if (!passportId || passports[passportId]) return;
    setPassports((p) => ({ ...p, [passportId]: { state: "loading" } }));
    const file = passportId.replace(/[:/]/g, "_") + ".json";
    fetch(`data/passports/${file}`)
      .then((r) => {
        // 404 is not an error here: it means no passport was ever issued for this subject, which is
        // a fact about the registry rather than a failure of ours. Reporting the two the same way
        // would hide a broken deploy behind a plausible "not found".
        if (r.status === 404) return null;
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d: { passport: Passport } | null) =>
        setPassports((p) => ({
          ...p,
          [passportId]: d ? { state: "ready", data: d.passport } : { state: "missing" },
        })),
      )
      .catch((e: Error) =>
        setPassports((p) => ({ ...p, [passportId]: { state: "error", why: e.message } })),
      );
  }, [passportId, passports]);

  // Keyboard flow: a hash change swaps the whole document but leaves focus where it was, so the
  // next Tab continues from the old page. Move focus to the top of the new one - except on first
  // paint, where stealing focus from the address bar would be wrong.
  useEffect(() => {
    document.title = TITLES[route] ?? (passportId ? `${passportId} - Provek` : "Provek");
    if (first.current) {
      first.current = false;
      return;
    }
    // preventScroll matters: focusing a container scrolls it into view, which on a short page
    // parks the reader below the masthead on a document they have not started reading. A new
    // route means the top of a new document, then focus at the start of its content.
    top.current?.focus({ preventScroll: true });
    window.scrollTo(0, 0);
  }, [route, passportId]);

  let body: React.ReactNode;
  if (passportId) {
    const p = passports[passportId] ?? { state: "loading" as const };
    body =
      p.state === "ready" ? (
        <PassportPage p={p.data} />
      ) : p.state === "missing" ? (
        <DeadEnd title="No passport for this subject">
          Nothing has been issued under <code className="font-mono text-xs">{passportId}</code>. That
          is a statement about our registry, not about the subject: an unmeasured business is not a
          failing one.
        </DeadEnd>
      ) : p.state === "error" ? (
        <DeadEnd title="Passport unavailable">
          The record exists in the registry but could not be read ({p.why}). This is our failure to
          serve it, and it says nothing about the subject.
        </DeadEnd>
      ) : (
        <PassportSkeleton />
      );
  } else if (route === "#/registry") {
    body =
      reg.state === "ready" ? (
        <Registry reg={reg.data} />
      ) : reg.state === "error" ? (
        <DeadEnd title="Registry unavailable">
          The registry file could not be read ({reg.why}). This is our failure to serve it, not a
          statement about any subject.
        </DeadEnd>
      ) : (
        <TableSkeleton />
      );
  } else if (route === "#/apply") {
    body = <Apply />;
  } else if (route === "#/method") {
    body = <Method />;
  } else if (route === "#/" || route === "") {
    body = <Landing reg={reg.state === "ready" ? reg.data : null} />;
  } else {
    // An unknown hash used to fall through to the landing page. Silently answering a different
    // question than the one asked is the same class of defect as a swallowed error.
    body = <DeadEnd title="No such page">
      Nothing is served at <code className="font-mono text-xs">{route}</code>.
    </DeadEnd>;
  }

  return (
    <div className="min-h-screen flex flex-col">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-10 focus:bg-[var(--color-paper)] focus:border focus:border-[var(--color-line-2)] focus:px-3 focus:py-2 focus:text-sm"
      >
        Skip to content
      </a>
      <Masthead route={route} />
      <div id="main" ref={top} tabIndex={-1} className="flex-1 outline-none">
        {body}
      </div>
      <Footer />
    </div>
  );
}
