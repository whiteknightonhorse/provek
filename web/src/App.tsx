/** Path routing, hand-rolled, and rendered to static HTML at build time.
 *
 * WHY NOT HASH, ANY MORE. Routing was by hash until 2026-08-20, which meant twelve screens shared
 * one crawlable URL: a search engine never sees anything after the `#`, so the registry and every
 * passport had no address to index, cite, or archive. That was not merely an SEO problem — D-01
 * requires a passport to stand alone and be readable a year later, and a document that exists only
 * as a fragment behind an empty `<body>` cannot be linked from a due-diligence memo. The routing
 * violated the product's own specification before Google entered the question.
 *
 * A router library would still add a dependency to solve five static routes. What changed is that
 * the same components now render twice: once in Node at build time into real HTML files, and once
 * in the browser to take over. One component set, one artefact set — which keeps D-10 intact
 * rather than introducing a second renderer that can drift. */

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

/** Server-rendered pages arrive with their data already inlined, so the first paint carries the
 * verdict rather than a skeleton — which is the whole point for a reader who does not run
 * JavaScript, and for an answer engine, which mostly does not. */
declare global {
  interface Window {
    __PROVEK__?: { registry?: R; passport?: Passport };
  }
}

const norm = (p: string) => (p.endsWith("/") ? p : p + "/");

function useRoute(initial: string) {
  const [route, setRoute] = useState(initial);
  useEffect(() => {
    const on = () => setRoute(norm(window.location.pathname));
    addEventListener("popstate", on);
    // Intercept same-origin clicks so navigation stays instant without a router dependency.
    const click = (e: MouseEvent) => {
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      const a = (e.target as HTMLElement)?.closest?.("a");
      if (!a) return;
      const href = a.getAttribute("href");
      if (!href || !href.startsWith("/") || a.target === "_blank") return;
      e.preventDefault();
      history.pushState(null, "", href);
      setRoute(norm(href));
    };
    addEventListener("click", click);
    return () => {
      removeEventListener("popstate", on);
      removeEventListener("click", click);
    };
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

/** Skeletons carry the shape of what is coming, not a generic shimmer. */
function TableSkeleton() {
  return (
    <Page>
      <div className="min-h-[100svh]">
        <Bar w="10rem" h="1.75rem" />
        <div className="mt-6 bg-[var(--color-paper)] border border-[var(--color-line)]">
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
        <div className="mt-6 bg-[var(--color-paper)] border border-[var(--color-line)] p-5 space-y-5">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="space-y-2">
              <Bar w="12rem" h="1rem" />
              <Bar w="100%" h="2rem" />
            </div>
          ))}
        </div>
      </div>
    </Page>
  );
}

/** One shape for every dead end, so that the page always names which one it is. */
export function DeadEnd({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Page>
      <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
      <p className="mt-2 max-w-[46rem] text-sm text-[var(--color-ink-2)]">{children}</p>
      <p className="mt-6 text-sm">
        <a href="/registry/" className="text-[var(--color-accent)] hover:underline">
          Back to the registry
        </a>
      </p>
    </Page>
  );
}

export const TITLES: Record<string, string> = {
  "/": "Provek - evidence, not claims",
  "/registry/": "Registry - Provek",
  "/method/": "Method - Provek",
  "/apply/": "Request verification - Provek",
};

/** The one place that decides what a route renders — shared by the browser and by the build-time
 * renderer, so a page cannot exist in one and not the other. */
export function Body({
  route,
  reg,
  passport,
}: {
  route: string;
  reg: Load<R>;
  passport: Load<Passport> | null;
}) {
  if (route.startsWith("/p/")) {
    const p = passport ?? { state: "loading" as const };
    if (p.state === "ready") return <PassportPage p={p.data} />;
    if (p.state === "missing")
      return (
        <DeadEnd title="No passport for this subject">
          Nothing has been issued under this identifier. That is a statement about our registry, not
          about the subject: an unmeasured business is not a failing one.
        </DeadEnd>
      );
    if (p.state === "error")
      return (
        <DeadEnd title="Passport unavailable">
          The record exists in the registry but could not be read ({p.why}). This is our failure to
          serve it, and it says nothing about the subject.
        </DeadEnd>
      );
    return <PassportSkeleton />;
  }
  if (route === "/registry/") {
    if (reg.state === "ready") return <Registry reg={reg.data} />;
    if (reg.state === "error")
      return (
        <DeadEnd title="Registry unavailable">
          The registry file could not be read ({reg.why}). This is our failure to serve it, not a
          statement about any subject.
        </DeadEnd>
      );
    return <TableSkeleton />;
  }
  if (route === "/apply/") return <Apply />;
  if (route === "/method/") return <Method />;
  if (route === "/") return <Landing reg={reg.state === "ready" ? reg.data : null} />;
  return (
    <DeadEnd title="No such page">
      Nothing is served at <code className="font-mono text-xs">{route}</code>.
    </DeadEnd>
  );
}

export function Shell({
  route,
  children,
  containerRef,
}: {
  route: string;
  children: React.ReactNode;
  containerRef?: React.Ref<HTMLDivElement>;
}) {
  return (
    <div className="min-h-screen flex flex-col">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-10 focus:bg-[var(--color-paper)] focus:border focus:border-[var(--color-line-2)] focus:px-3 focus:py-2 focus:text-sm"
      >
        Skip to content
      </a>
      <Masthead route={route} />
      <div id="main" ref={containerRef} tabIndex={-1} className="flex-1 outline-none">
        {children}
      </div>
      <Footer />
    </div>
  );
}

export default function App() {
  const route = useRoute(norm(typeof location === "undefined" ? "/" : location.pathname));
  const inlined = typeof window !== "undefined" ? window.__PROVEK__ : undefined;

  const [reg, setReg] = useState<Load<R>>(
    inlined?.registry ? { state: "ready", data: inlined.registry } : { state: "loading" },
  );
  const [passports, setPassports] = useState<Record<string, Load<Passport>>>(() =>
    inlined?.passport
      ? { [inlined.passport.subject_id]: { state: "ready", data: inlined.passport } }
      : {},
  );
  const first = useRef(true);
  const top = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (reg.state === "ready") return;
    fetch("/data/registry.json")
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((d: R) => setReg({ state: "ready", data: d }))
      .catch((e: Error) => setReg({ state: "error", why: e.message }));
  }, [reg.state]);

  const slugInRoute = route.startsWith("/p/") ? route.slice(3).replace(/\/$/, "") : null;
  const known =
    slugInRoute && reg.state === "ready"
      ? reg.data.subjects.find((s) => s.subject_id.replace(/[:/]/g, "_") === slugInRoute)
      : undefined;
  const passportId = known?.subject_id ?? null;

  useEffect(() => {
    if (!slugInRoute) return;
    const key = passportId ?? slugInRoute;
    if (passports[key]) return;
    setPassports((p) => ({ ...p, [key]: { state: "loading" } }));
    fetch(`/data/passports/${slugInRoute}.json`)
      .then((r) => {
        // 404 is not an error here: it means no passport was ever issued for this subject, which is
        // a fact about the registry rather than a failure of ours.
        if (r.status === 404) return null;
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d: { passport: Passport } | null) =>
        setPassports((p) => ({ ...p, [key]: d ? { state: "ready", data: d.passport } : { state: "missing" } })),
      )
      .catch((e: Error) => setPassports((p) => ({ ...p, [key]: { state: "error", why: e.message } })));
  }, [slugInRoute, passportId, passports]);

  useEffect(() => {
    document.title = TITLES[route] ?? (passportId ? `${passportId} - Provek` : "Provek");
    if (first.current) {
      first.current = false;
      return;
    }
    // preventScroll matters: focusing a container scrolls it into view, which on a short page
    // parks the reader below the masthead on a document they have not started reading.
    top.current?.focus({ preventScroll: true });
    window.scrollTo(0, 0);
  }, [route, passportId]);

  const passport = slugInRoute ? (passports[passportId ?? slugInRoute] ?? { state: "loading" as const }) : null;

  return (
    <Shell route={route} containerRef={top}>
      <Body route={route} reg={reg} passport={passport} />
    </Shell>
  );
}
