/** Build-time renderer. Runs in Node, renders the SAME components the browser renders.
 *
 * Two renderers would drift; D-10 says the human surface reads the artefacts the machines read,
 * and a second templating path would quietly become a second source of truth. So this imports
 * `Shell` and `Body` from the app rather than reproducing them. */
import { render as toString } from "preact-render-to-string";
import { Body, PRERENDER_ROUTE, Shell, TITLES } from "./App";
import type { Passport, Registry as R } from "./types";

export function renderRoute(route: string, reg: R | null, passport: Passport | null): string {
  return toString(
    <Shell route={route}>
      <Body
        route={route}
        reg={reg ? { state: "ready", data: reg } : { state: "loading" }}
        passport={
          route.startsWith("/p/")
            ? passport
              ? { state: "ready", data: passport }
              : { state: "missing" }
            : null
        }
      />
    </Shell>,
  );
}

/** A method note, in the site's own chrome and nothing else.
 *
 * The note's body is HTML built by `web/notes/emit.mjs` from committed prose - it is a document,
 * not a component, and it carries no state for a browser to take over. What it must NOT do is
 * reproduce the masthead and the footer: a second copy of the chrome is a second thing to drift,
 * and the whole reason `renderRoute` exists is that there is one component set. So the note is
 * poured into the same `Shell`, and inherits every token and every rule by construction. */
export function renderStatic(route: string, html: string): string {
  return toString(
    <Shell route={route}>
      <main className="mx-auto max-w-[1180px] px-5 py-8">
        <div dangerouslySetInnerHTML={{ __html: html }} />
      </main>
    </Shell>,
  );
}

export { PRERENDER_ROUTE, TITLES };
