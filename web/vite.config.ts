import { defineConfig } from "vite";
import preact from "@preact/preset-vite";
import tailwindcss from "@tailwindcss/vite";

/** Preact through the compat layer, not React.
 *
 * This surface is five static routes rendered from two JSON files. React was shipping 225 kB to
 * do hash routing and paint four documents, which the phase-4 audit recorded as the one open
 * performance item. `preact/compat` keeps every hook and every component untouched - the source
 * still imports from "react" - and removes the bulk of the runtime.
 *
 * The trade is real and worth naming: any future dependency that reaches into React internals
 * rather than its public API will not work here. Nothing in this project does, and a verification
 * registry is unlikely to grow one. If it ever does, delete this file's preset and reinstall
 * react-dom; nothing else changes. */
export default defineConfig({
  plugins: [preact(), tailwindcss()],
  base: "/",
});
