/** The one permitted link from a template page to the instrument (ADR-0011 section 6.4, SPEC 3.7
 * item 5). Fixed text, one component, rendered once per template page and once on the index -
 * never retyped, so "once per page" is a fact about where this is imported rather than a promise
 * a second copy could quietly break. `tests/test_build_funnel_strip_once.py` counts occurrences
 * of this component's own link text under `dist/build/`, not of `/apply/` in general. */
import { Strip } from "./Chrome";

export function FunnelStrip() {
  return (
    <Strip tone="info">
      <strong>When it runs from a public repository, you can request verification.</strong> The
      measurement is independent of this page: the scorer reads the repository&rsquo;s evidence,
      and nothing here is one of its inputs. The result may be any level, including{" "}
      <em>not measured</em>.{" "}
      <a href="/apply/" className="text-[var(--color-accent)] hover:underline">
        Request verification &rarr;
      </a>
    </Strip>
  );
}
