/** Build-time renderer. Runs in Node, renders the SAME components the browser renders.
 *
 * Two renderers would drift; D-10 says the human surface reads the artefacts the machines read,
 * and a second templating path would quietly become a second source of truth. So this imports
 * `Shell` and `Body` from the app rather than reproducing them. */
import { render as toString } from "preact-render-to-string";
import { Body, Shell, TITLES } from "./App";
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

export { TITLES };
