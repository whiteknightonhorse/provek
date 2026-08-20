/** Hash routing, hand-rolled.
 *
 * A router library would add a dependency and a build-size cost to solve four static routes on a
 * site that is deliberately small. If the route table grows past a handful, revisit. */

import { useEffect, useState } from "react";
import { Footer, Masthead, Page } from "./components/Chrome";
import Landing from "./pages/Landing";
import Registry from "./pages/Registry";
import PassportPage from "./pages/Passport";
import Apply from "./pages/Apply";
import Method from "./pages/Method";
import type { Passport, Registry as R } from "./types";

type Load<T> = { state: "loading" } | { state: "error"; why: string } | { state: "ready"; data: T };

function useRoute() {
  const [route, setRoute] = useState(window.location.hash || "#/");
  useEffect(() => {
    const on = () => setRoute(window.location.hash || "#/");
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  return route;
}

/** Skeleton with headers already present - the page must not reflow when data lands (from NVD). */
function TableSkeleton() {
  return (
    <Page>
      <div className="h-7 w-40 bg-[var(--color-line)]" />
      <div className="mt-6 bg-[var(--color-paper)] border border-[var(--color-line)]">
        <div className="grid grid-cols-5 gap-4 border-b border-[var(--color-line-2)] px-4 py-2.5 text-sm font-semibold">
          <span>Subject</span><span>Status</span><span>Autonomy</span><span>Verifier</span><span>Valid until</span>
        </div>
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="grid grid-cols-5 gap-4 border-b border-[var(--color-line)] px-4 py-3">
            {Array.from({ length: 5 }).map((__, j) => (
              <div key={j} className="h-4 bg-[var(--color-line)] rounded-sm" />
            ))}
          </div>
        ))}
      </div>
    </Page>
  );
}

export default function App() {
  const route = useRoute();
  const [reg, setReg] = useState<Load<R>>({ state: "loading" });
  const [passports, setPassports] = useState<Record<string, Passport>>({});

  useEffect(() => {
    fetch("data/registry.json")
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((d: R) => setReg({ state: "ready", data: d }))
      .catch((e: Error) =>
        // An error state that names the cause. "Could not load" alone would be the same defect the
        // product exists to expose: one message covering several states of the world.
        setReg({ state: "error", why: e.message }),
      );
  }, []);

  const passportId = route.startsWith("#/p/") ? decodeURIComponent(route.slice(4)) : null;

  useEffect(() => {
    if (!passportId || passports[passportId]) return;
    const file = passportId.replace(/[:/]/g, "_") + ".json";
    fetch(`data/passports/${file}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((d: { passport: Passport }) =>
        setPassports((p) => ({ ...p, [passportId]: d.passport })),
      )
      .catch(() => undefined);
  }, [passportId, passports]);

  let body: React.ReactNode;
  if (passportId) {
    const p = passports[passportId];
    body = p ? <PassportPage p={p} /> : <TableSkeleton />;
  } else if (route === "#/registry") {
    body =
      reg.state === "ready" ? (
        <Registry reg={reg.data} />
      ) : reg.state === "error" ? (
        <Page>
          <h1 className="text-2xl font-semibold">Registry unavailable</h1>
          <p className="mt-2 text-sm text-[var(--color-ink-2)]">
            The registry file could not be read ({reg.why}). This is our failure to serve it, not a
            statement about any subject.
          </p>
        </Page>
      ) : (
        <TableSkeleton />
      );
  } else if (route === "#/apply") {
    body = <Apply />;
  } else if (route === "#/method") {
    body = <Method />;
  } else {
    body = <Landing count={reg.state === "ready" ? reg.data.count : 0} />;
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Masthead route={route} />
      <div className="flex-1">{body}</div>
      <Footer />
    </div>
  );
}
