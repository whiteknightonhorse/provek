import { render } from "preact-render-to-string";
import { useEffect, useMemo, useRef, useState } from "preact/compat";
import { Fragment, jsx, jsxs } from "preact/jsx-runtime";
//#region src/components/Chrome.tsx
/** Shell: masthead, nav, footer. Phase-2 slots are reserved here and rendered as disabled, never
* announced as features that exist (decision D-05). */
function Masthead({ route }) {
	const link = (href, label, active) => /* @__PURE__ */ jsx("a", {
		href,
		"aria-current": active ? "page" : void 0,
		className: "px-3 py-2.5 min-h-11 inline-flex items-center text-sm border-b-2 -mb-px " + (active ? "border-[var(--color-ink)] text-[var(--color-ink)]" : "border-transparent text-[var(--color-ink-2)] hover:text-[var(--color-ink)]"),
		children: label
	}, href);
	return /* @__PURE__ */ jsx("header", {
		className: "bg-[var(--color-paper)] border-b border-[var(--color-line)]",
		children: /* @__PURE__ */ jsxs("div", {
			className: "mx-auto max-w-[1180px] px-5",
			children: [/* @__PURE__ */ jsxs("div", {
				className: "flex items-center justify-between py-3",
				children: [/* @__PURE__ */ jsxs("a", {
					href: "/",
					className: "flex items-baseline gap-2 min-h-11 py-2",
					children: [/* @__PURE__ */ jsx("span", {
						className: "text-lg font-semibold tracking-tight",
						children: "Provek"
					}), /* @__PURE__ */ jsx("span", {
						className: "text-xs text-[var(--color-ink-3)]",
						children: "evidence, not claims"
					})]
				}), /* @__PURE__ */ jsx("a", {
					href: "/apply/",
					className: "text-sm border border-[var(--color-line-2)] px-3.5 min-h-11 inline-flex items-center hover:bg-[var(--color-paper-2)]",
					children: "Request verification"
				})]
			}), /* @__PURE__ */ jsxs("nav", {
				className: "flex gap-1 border-t border-[var(--color-line)] pt-1",
				"aria-label": "Main",
				children: [
					link("/registry/", "Registry", route.startsWith("/registry") || route.startsWith("/p/")),
					link("/method/", "Method", route === "/method/"),
					/* @__PURE__ */ jsx("span", {
						className: "px-3 py-2.5 min-h-11 inline-flex items-center text-sm text-[var(--color-ink-disabled)] cursor-default select-none",
						"aria-disabled": "true",
						"aria-label": "Corpus, not available",
						children: "Corpus"
					})
				]
			})]
		})
	});
}
function Footer() {
	return /* @__PURE__ */ jsx("footer", {
		className: "mt-16 border-t border-[var(--color-line)] bg-[var(--color-paper)]",
		children: /* @__PURE__ */ jsxs("div", {
			className: "mx-auto max-w-[1180px] px-5 py-8 text-xs text-[var(--color-ink-3)] space-y-2",
			children: [
				/* @__PURE__ */ jsxs("p", { children: [
					"The score measures ",
					/* @__PURE__ */ jsx("strong", {
						className: "text-[var(--color-ink-2)]",
						children: "autonomy"
					}),
					". It does not measure reliability, decision quality, profitability, or the presence of an accountable party."
				] }),
				/* @__PURE__ */ jsx("p", { children: "Methodology is published in full. A verdict is reproducible by a third party from the same inputs — if it were not, this would be a brand rather than a standard." }),
				/* @__PURE__ */ jsx("p", { children: "provek.dev" })
			]
		})
	});
}
function Page({ children }) {
	return /* @__PURE__ */ jsx("main", {
		className: "mx-auto max-w-[1180px] px-5 py-8",
		children
	});
}
/** A finding strip. Positive and negative share one rhythm - borrowed from SSL Labs, where
* "does not support PQC" sits in the same stack as the passing lines rather than hiding. */
function Strip({ tone, children }) {
	return /* @__PURE__ */ jsx("div", {
		className: "border border-[var(--color-line)] px-4 py-3 text-sm",
		style: { background: tone === "pass" ? "var(--c-wash-pass)" : tone === "warn" ? "var(--c-wash-warn)" : "var(--c-wash-info)" },
		children
	});
}
/** Dense two-column label/value table. Sub-detail goes inside the cell, never in a nested card. */
function Facts({ rows }) {
	return /* @__PURE__ */ jsx("dl", {
		className: "divide-y divide-[var(--color-line)] border-y border-[var(--color-line)]",
		children: rows.map(([k, v]) => /* @__PURE__ */ jsxs("div", {
			className: "grid grid-cols-1 gap-1 py-2 sm:grid-cols-[minmax(9rem,14rem)_1fr] sm:gap-4",
			children: [/* @__PURE__ */ jsx("dt", {
				className: "text-sm text-[var(--color-ink-2)]",
				children: k
			}), /* @__PURE__ */ jsx("dd", {
				className: "text-sm",
				children: v
			})]
		}, k))
	});
}
//#endregion
//#region src/components/Measured.tsx
/** Rendering of a measured value versus an absent one.
*
* DECISION D-03, and it is the single most load-bearing rule in this interface: an unmeasured
* quantity renders as its own state with its own glyph and its own neutral colour. It never
* renders as 0, never as an empty cell, never as a dash that could be mistaken for either.
*
* The pattern is borrowed from OpenSSF Scorecard, where an unevaluable check shows "?" in grey
* while a genuinely failing check shows a measured 0 in red. Two different states of the world,
* two different appearances - proven in a product people already trust. */
var REASON_TEXT = {
	nothing_qualified: "the check ran and nothing qualified",
	check_did_not_run: "the check did not run",
	unreadable: "the source could not be read"
};
function AbsentMark({ reason }) {
	return /* @__PURE__ */ jsxs("span", {
		className: "inline-flex items-baseline gap-1.5",
		title: reason ? REASON_TEXT[reason] ?? reason : "not measured",
		children: [
			/* @__PURE__ */ jsx("span", {
				className: "sr-only",
				children: reason ? `not measured: ${REASON_TEXT[reason] ?? reason}` : "not measured, reason not stated"
			}),
			/* @__PURE__ */ jsx("span", {
				className: "slot",
				"aria-hidden": "true"
			}),
			/* @__PURE__ */ jsx("span", {
				className: "slot--label",
				"aria-hidden": "true",
				children: "not measured"
			})
		]
	});
}
/** The 0..100 projection, or its absence with the reason. */
function Projection({ value, absentReason }) {
	if (value === null) return /* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx(AbsentMark, { reason: absentReason }), /* @__PURE__ */ jsx("p", {
		className: "mt-1 text-xs text-[var(--color-ink-3)] max-w-[22rem]",
		children: "A zero here would mean “measured, and fully non-autonomous” — an entirely different claim about the world."
	})] });
	return /* @__PURE__ */ jsxs("div", {
		className: "flex items-baseline gap-2",
		children: [/* @__PURE__ */ jsx("span", {
			className: "text-5xl font-semibold tabular-nums leading-none",
			children: value
		}), /* @__PURE__ */ jsx("span", {
			className: "text-sm text-[var(--color-ink-3)]",
			children: "/ 100"
		})]
	});
}
/** Level rail: the number or "?" plus a colour bar underneath. Anatomy from OpenSSF Scorecard. */
function LevelRail({ level, measured }) {
	const n = measured ? Number(level.replace("L", "")) : null;
	return /* @__PURE__ */ jsxs("div", {
		className: "w-14 shrink-0 text-center",
		children: [/* @__PURE__ */ jsx("div", {
			className: "font-mono text-lg leading-tight",
			style: { color: measured ? "var(--color-ink)" : "var(--color-unknown)" },
			children: measured ? level : /* @__PURE__ */ jsxs(Fragment, { children: [/* @__PURE__ */ jsx("span", {
				className: "slot",
				"aria-hidden": "true"
			}), /* @__PURE__ */ jsx("span", {
				className: "sr-only",
				children: "not measured"
			})] })
		}), measured && /* @__PURE__ */ jsx("div", {
			className: "mt-1 h-[3px] w-full rounded-sm bg-[var(--color-line)]",
			"aria-hidden": "true",
			children: /* @__PURE__ */ jsx("div", {
				className: "h-full rounded-sm bg-[var(--color-ink-2)]",
				style: { width: `${(n ?? 0) / 5 * 100}%` }
			})
		})]
	});
}
//#endregion
//#region src/types.ts
/** The pipeline's slug, and deliberately the same derivation.
*
* `git:whiteknightonhorse/APIbase` -> `git_whiteknightonhorse_APIbase`. The passport JSON is
* written under this name by `FileTransport`, so a page URL and its machine record cannot drift
* apart: one rule, two consumers. */
function slug(subjectId) {
	return subjectId.replace(/[:/]/g, "_");
}
/** Status BY TIME, computed at read time — and it has to be (A2).
*
* `Passport.effective_status` implements ABI-15-5 in Python: a verified record lapses to `stale`
* on its own, with no event. The web never computed it, so a static registry generated today would
* go on saying `verified` for ever. On 2026-09-19 every current row lapses in the machine sense
* while the page kept the older word — "no news" and "expired" rendered identically, which is the
* founding defect in its temporal form.
*
* DESIGN rule 3 says nothing is computed for display. This is the recorded carve-out: staleness is
* DEFINED as a read-time computation. A value that expires cannot be baked into the artefact that
* expires with it. */
function effectiveStatus(status, validUntil, now = /* @__PURE__ */ new Date()) {
	if (status !== "verified") return status;
	return now >= new Date(validUntil) ? "stale" : "verified";
}
function daysUntil(validUntil, now = /* @__PURE__ */ new Date()) {
	return Math.ceil((new Date(validUntil).getTime() - now.getTime()) / 864e5);
}
//#endregion
//#region src/pages/Landing.tsx
/** The only screen allowed air. Content follows docs/WHY_GET_VERIFIED.md, including its limits -
* those are part of the pitch, not a caveat to bury. */
/** `reg` is null while the registry is still loading. Rendering a 0 or an invented row there
* would state a measured fact we do not have yet - a fabrication in the one place this product
* promises never to fabricate. */
function Landing({ reg }) {
	const count = reg?.count ?? null;
	const paced = useRef(null);
	useEffect(() => {
		const el = paced.current;
		if (!el || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
		const items = Array.from(el.children);
		const release = (node) => {
			node.dataset.seen = "";
		};
		el.classList.add("paced--armed");
		for (const item of items) {
			const r = item.getBoundingClientRect();
			if (r.top < window.innerHeight && r.bottom > 0) release(item);
		}
		const io = new IntersectionObserver((entries) => {
			for (const e of entries) {
				if (!e.isIntersecting) continue;
				release(e.target);
				io.unobserve(e.target);
			}
		}, { rootMargin: "0px 0px -12% 0px" });
		for (const item of items) if (!item.dataset.seen) io.observe(item);
		const valve = window.setTimeout(() => items.forEach(release), 2e3);
		return () => {
			io.disconnect();
			window.clearTimeout(valve);
		};
	}, []);
	const preview = reg?.subjects.slice(0, 4) ?? [];
	return /* @__PURE__ */ jsxs(Page, { children: [
		/* @__PURE__ */ jsxs("div", {
			className: "grid gap-10 lg:grid-cols-[minmax(0,42rem)_minmax(0,1fr)] lg:gap-14",
			children: [/* @__PURE__ */ jsxs("section", {
				className: "pt-6",
				children: [
					/* @__PURE__ */ jsx("h1", {
						className: "text-[2.1rem] leading-[1.15] font-semibold tracking-tight",
						children: "Your customers cannot tell you apart from a company that wrote “AI-powered” on a landing page."
					}),
					/* @__PURE__ */ jsx("p", {
						className: "mt-5 text-[1.05rem] leading-relaxed text-[var(--color-ink-2)]",
						children: "That is not a marketing problem, and marketing cannot fix it: any claim you make, a competitor can make more loudly. It is a verification problem."
					}),
					/* @__PURE__ */ jsx("p", {
						className: "mt-4 text-[1.05rem] leading-relaxed text-[var(--color-ink-2)]",
						children: "Provek measures, per business operation, how much of your company runs without a human in the loop — and publishes the measurements behind every number, including the ones that could not be taken."
					}),
					/* @__PURE__ */ jsxs("div", {
						className: "mt-7 flex flex-wrap gap-3",
						children: [/* @__PURE__ */ jsx("a", {
							href: "/apply/",
							className: "border border-[var(--color-ink)] bg-[var(--color-ink)] text-[var(--color-paper)] px-4 py-2 text-sm",
							children: "Request verification"
						}), /* @__PURE__ */ jsxs("a", {
							href: "/registry/",
							className: "border border-[var(--color-line-2)] px-4 py-2 text-sm hover:bg-[var(--color-paper)]",
							children: ["See the registry", count === null ? "" : ` (${count})`]
						})]
					})
				]
			}), /* @__PURE__ */ jsxs("aside", {
				className: "lg:pt-8",
				children: [/* @__PURE__ */ jsx("h2", {
					className: "text-xs uppercase tracking-wide text-[var(--color-ink-3)]",
					children: "The registry, right now"
				}), reg === null ? /* @__PURE__ */ jsx("div", {
					className: "mt-4 space-y-3",
					"aria-hidden": "true",
					children: Array.from({ length: 4 }).map((_, i) => /* @__PURE__ */ jsx("div", { className: "skeleton-bar h-10 bg-[var(--color-line)] rounded-sm" }, i))
				}) : /* @__PURE__ */ jsxs(Fragment, { children: [/* @__PURE__ */ jsx("ul", {
					className: "mt-4 divide-y divide-[var(--color-line)] border-y border-[var(--color-line)]",
					children: preview.map((s2) => /* @__PURE__ */ jsxs("li", {
						className: "flex items-baseline justify-between gap-4 py-2.5",
						children: [/* @__PURE__ */ jsx("a", {
							href: `/p/${slug(s2.subject_id)}/`,
							className: "text-sm text-[var(--color-accent)] hover:underline truncate",
							children: s2.subject_id.split("/").pop()
						}), /* @__PURE__ */ jsx("span", {
							className: "shrink-0 text-sm tabular-nums",
							children: s2.projection === null ? /* @__PURE__ */ jsx(AbsentMark, { reason: s2.projection_absent_reason }) : /* @__PURE__ */ jsxs(Fragment, { children: [s2.projection, /* @__PURE__ */ jsx("span", {
								className: "text-[var(--color-ink-3)]",
								children: " / 100"
							})] })
						})]
					}, s2.subject_id))
				}), /* @__PURE__ */ jsxs("p", {
					className: "mt-3 text-xs text-[var(--color-ink-3)]",
					children: [
						count,
						" records",
						reg.subjects.every((x) => x.verifier_affiliation === "same_owner") ? ", every one of them the operator’s own and marked " : ", of which " + reg.subjects.filter((x) => x.verifier_affiliation === "same_owner").length + " are the operator’s own and marked ",
						/* @__PURE__ */ jsx("span", {
							style: { color: "var(--color-warn)" },
							children: "affiliated"
						}),
						". Saying so is the point.",
						" ",
						/* @__PURE__ */ jsx("a", {
							href: "/registry/",
							className: "text-[var(--color-accent)] hover:underline",
							children: "See all"
						}),
						"."
					]
				})] })]
			})]
		}),
		/* @__PURE__ */ jsxs("section", {
			className: "mt-14 max-w-[46rem]",
			children: [/* @__PURE__ */ jsx("h2", {
				className: "text-lg font-semibold",
				children: "Why this is worth your time today"
			}), /* @__PURE__ */ jsxs("div", {
				className: "mt-4 space-y-3",
				children: [
					/* @__PURE__ */ jsxs(Strip, {
						tone: "pass",
						children: [/* @__PURE__ */ jsx("strong", { children: "It is an artefact for your customers, not for ours." }), " Your buyers already ask how much of your product is really automated. A verified passport is the one answer a competitor running an AI theatre cannot copy — copying it requires actually being autonomous."]
					}),
					/* @__PURE__ */ jsxs(Strip, {
						tone: "pass",
						children: [/* @__PURE__ */ jsx("strong", { children: "A regulatory dossier you will need anyway." }), " At some point your counsel has to argue about who controls what. A control map is evidence input for that argument, built beforehand, by a third party, with a timestamp."]
					}),
					/* @__PURE__ */ jsxs(Strip, {
						tone: "info",
						children: [/* @__PURE__ */ jsx("strong", { children: "It costs nothing right now." }), " Early passports are free. That is not a favour: a registry with no entries is worth nothing, and we need the first ones as much as you do. Saying so is cheaper than pretending otherwise."]
					})
				]
			})]
		}),
		/* @__PURE__ */ jsxs("section", {
			className: "mt-12 max-w-[46rem]",
			children: [
				/* @__PURE__ */ jsx("h2", {
					className: "text-lg font-semibold",
					children: "The limits, up front"
				}),
				/* @__PURE__ */ jsx("p", {
					className: "mt-2 text-sm text-[var(--color-ink-2)]",
					children: "We would rather lose you as a subject than have you discover these later."
				}),
				/* @__PURE__ */ jsxs("ul", {
					ref: paced,
					className: "paced mt-4 space-y-3 text-sm text-[var(--color-ink-2)]",
					children: [
						/* @__PURE__ */ jsxs("li", {
							className: "border-l border-[var(--color-line-2)] pl-3.5",
							children: [/* @__PURE__ */ jsx("strong", {
								className: "text-[var(--color-ink)]",
								children: "We measure autonomy, not quality."
							}), " The passport says nothing about whether your decisions are good, whether you are profitable, or whether you are safe to rely on."]
						}),
						/* @__PURE__ */ jsxs("li", {
							className: "border-l border-[var(--color-line-2)] pl-3.5",
							children: [
								/* @__PURE__ */ jsx("strong", {
									className: "text-[var(--color-ink)]",
									children: "Some claims are not verifiable at reasonable cost."
								}),
								" ",
								"“No human wrote this commit” is one of them. Where a signal is probabilistic we publish it as probabilistic, and it never becomes a verdict."
							]
						}),
						/* @__PURE__ */ jsxs("li", {
							className: "border-l border-[var(--color-line-2)] pl-3.5",
							children: [
								/* @__PURE__ */ jsx("strong", {
									className: "text-[var(--color-ink)]",
									children: "A control map proves a path exists; it can never prove none was missed."
								}),
								" ",
								"Every map publishes its own coverage."
							]
						}),
						/* @__PURE__ */ jsxs("li", {
							className: "border-l border-[var(--color-line-2)] pl-3.5",
							children: [
								/* @__PURE__ */ jsx("strong", {
									className: "text-[var(--color-ink)]",
									children: "Without a mandate we do not touch your production."
								}),
								" ",
								"Probing a live system without one is an incident, not a verification."
							]
						})
					]
				})
			]
		}),
		/* @__PURE__ */ jsxs("section", {
			className: "mt-12 max-w-[46rem]",
			children: [/* @__PURE__ */ jsx("h2", {
				className: "text-lg font-semibold",
				children: "What we never do"
			}), /* @__PURE__ */ jsx("p", {
				className: "mt-2 text-sm text-[var(--color-ink-2)]",
				children: "We never hold your funds. We never take custody of your keys. We never store your secrets — they are redacted before they become an artefact. We never verify anyone who did not ask."
			})]
		})
	] });
}
//#endregion
//#region src/pages/Registry.tsx
/** The listing. Dense, plain, and honest about its size (decision D-04).
*
* Eight rows exist. All are affiliated. We do not invent companies to fill the table: fabricated
* entries in a trust registry would be precisely the thing this product exists to expose. So the
* near-empty state is designed rather than apologised for. */
function shortId(id) {
	const i = id.indexOf("/");
	return i === -1 ? id : id.slice(i + 1);
}
function Registry({ reg }) {
	const [q, setQ] = useState("");
	const rows = useMemo(() => reg.subjects.filter((s) => s.subject_id.toLowerCase().includes(q.toLowerCase())), [reg.subjects, q]);
	return /* @__PURE__ */ jsxs(Page, { children: [
		/* @__PURE__ */ jsx("h1", {
			className: "text-2xl font-semibold tracking-tight",
			children: "Registry"
		}),
		/* @__PURE__ */ jsxs("p", {
			className: "mt-1 text-sm text-[var(--color-ink-2)] max-w-[46rem]",
			children: [
				"Every business submitted to the method, what could be established about each, and the evidence behind it. Generated",
				" ",
				reg.generated_at.slice(0, 19).replace("T", " "),
				" UTC."
			]
		}),
		/* @__PURE__ */ jsx("div", {
			className: "mt-5 space-y-2",
			children: /* @__PURE__ */ jsxs(Strip, {
				tone: "info",
				children: [
					/* @__PURE__ */ jsxs("strong", { children: [reg.count, " records."] }),
					" ",
					reg.subjects.every((s2) => s2.verifier_affiliation === "same_owner") ? "All of them are the operator’s own systems, marked as affiliated." : `${reg.subjects.filter((s2) => s2.verifier_affiliation === "same_owner").length} of them are the operator\u2019s own systems, marked as affiliated.`,
					" ",
					"A registry of trust that padded itself with invented entries would be doing the exact thing it exists to detect, so it stays this size until real subjects grant a mandate.",
					reg.subjects.some((s2) => s2.projection_absent_reason === "unreadable") && /* @__PURE__ */ jsxs(Fragment, { children: [
						" ",
						/* @__PURE__ */ jsxs("strong", { children: [
							reg.subjects.filter((s2) => s2.projection_absent_reason === "unreadable").length,
							" ",
							"could not be measured at all:"
						] }),
						" ",
						"their sources do not answer a reader holding no credential. Evidence only we can reach is not evidence anyone else can recompute, so those rows carry no number rather than a number nobody could check."
					] })
				]
			})
		}),
		/* @__PURE__ */ jsxs("div", {
			className: "mt-6 flex flex-wrap items-baseline justify-between gap-3",
			children: [/* @__PURE__ */ jsxs("label", {
				className: "flex items-center gap-2 text-sm",
				children: [/* @__PURE__ */ jsx("span", {
					className: "text-[var(--color-ink-2)]",
					children: "Filter"
				}), /* @__PURE__ */ jsx("input", {
					value: q,
					onChange: (e) => setQ(e.target.value),
					placeholder: "subject",
					className: "border border-[var(--color-line-2)] bg-[var(--color-paper)] px-2.5 py-1.5 text-sm w-56"
				})]
			}), /* @__PURE__ */ jsx("p", {
				"aria-live": "polite",
				className: "text-sm text-[var(--color-ink-3)] tabular-nums",
				children: rows.length === reg.count ? `${reg.count} of ${reg.count}` : `${rows.length} of ${reg.count}`
			})]
		}),
		/* @__PURE__ */ jsx("div", {
			className: "mt-3 overflow-x-auto bg-[var(--color-paper)] border border-[var(--color-line)]",
			children: /* @__PURE__ */ jsxs("table", {
				className: "stack-table w-full text-sm",
				children: [/* @__PURE__ */ jsx("thead", { children: /* @__PURE__ */ jsxs("tr", {
					className: "border-b border-[var(--color-line-2)] text-left",
					children: [
						/* @__PURE__ */ jsx("th", {
							scope: "col",
							className: "px-4 py-2.5 font-semibold",
							children: "Subject"
						}),
						/* @__PURE__ */ jsx("th", {
							scope: "col",
							className: "px-4 py-2.5 font-semibold",
							children: "Status"
						}),
						/* @__PURE__ */ jsx("th", {
							scope: "col",
							className: "px-4 py-2.5 font-semibold",
							children: "Autonomy"
						}),
						/* @__PURE__ */ jsx("th", {
							scope: "col",
							className: "px-4 py-2.5 font-semibold",
							children: "Verifier"
						}),
						/* @__PURE__ */ jsx("th", {
							scope: "col",
							className: "px-4 py-2.5 font-semibold",
							children: "Valid until"
						}),
						/* @__PURE__ */ jsx("th", {
							scope: "col",
							className: "px-4 py-2.5",
							"aria-hidden": "true"
						})
					]
				}) }), /* @__PURE__ */ jsxs("tbody", {
					className: "divide-y divide-[var(--color-line)]",
					children: [rows.map((s) => /* @__PURE__ */ jsxs("tr", {
						className: "hover:bg-[var(--color-paper-2)]",
						children: [
							/* @__PURE__ */ jsxs("td", {
								className: "px-4 py-2.5",
								children: [/* @__PURE__ */ jsx("a", {
									href: `/p/${slug(s.subject_id)}/`,
									className: "text-[var(--color-accent)] hover:underline",
									children: shortId(s.subject_id)
								}), /* @__PURE__ */ jsx("div", {
									className: "text-xs text-[var(--color-ink-3)] font-mono",
									children: s.subject_id
								})]
							}),
							/* @__PURE__ */ jsx("td", {
								"data-label": "Status",
								className: "px-4 py-2.5",
								children: (() => {
									const eff = effectiveStatus(s.status, s.valid_until);
									return eff === "stale" ? /* @__PURE__ */ jsx("span", {
										style: { color: "var(--color-warn)" },
										title: "The evidence window has closed. The verdict was true when issued and has not been renewed.",
										children: "stale"
									}) : eff;
								})()
							}),
							/* @__PURE__ */ jsx("td", {
								"data-label": "Autonomy",
								className: "px-4 py-2.5 tabular-nums",
								children: s.projection === null ? /* @__PURE__ */ jsx(AbsentMark, { reason: s.projection_absent_reason }) : /* @__PURE__ */ jsxs("span", { children: [
									s.projection,
									" ",
									/* @__PURE__ */ jsx("span", {
										className: "text-[var(--color-ink-3)]",
										children: "/ 100"
									})
								] })
							}),
							/* @__PURE__ */ jsx("td", {
								"data-label": "Verifier",
								className: "px-4 py-2.5",
								children: s.verifier_affiliation === "same_owner" ? /* @__PURE__ */ jsx("span", {
									style: { color: "var(--color-warn)" },
									children: "affiliated"
								}) : /* @__PURE__ */ jsx("span", {
									className: "text-[var(--color-ink-2)]",
									children: "independent"
								})
							}),
							/* @__PURE__ */ jsx("td", {
								"data-label": "Valid until",
								className: "px-4 py-2.5 tabular-nums",
								children: s.valid_until.slice(0, 10)
							}),
							/* @__PURE__ */ jsx("td", { className: "px-4 py-2.5" })
						]
					}, s.subject_id)), rows.length === 0 && /* @__PURE__ */ jsx("tr", { children: /* @__PURE__ */ jsxs("td", {
						colSpan: 6,
						className: "px-4 py-10 text-center text-[var(--color-ink-3)]",
						children: [
							"Nothing matches “",
							q,
							"”. The registry holds ",
							reg.count,
							" records in total."
						]
					}) })]
				})]
			})
		}),
		/* @__PURE__ */ jsx("p", {
			className: "mt-4 text-xs text-[var(--color-ink-3)] max-w-[46rem]",
			children: reg.disclaimer
		})
	] });
}
//#endregion
//#region src/pages/Passport.tsx
/** The load-bearing screen (decision D-01).
*
* A consumer of evidence arrives here by a link from an email or a due-diligence memo and has
* never seen the landing page. So this page must stand alone, and it must still be readable a
* year from now - which is why provenance and protocol version are ON the page rather than in
* metadata. */
var OBS_LABEL = {
	signed_commit_share: "Share of commits with a verified signature",
	distinct_authors: "Distinct commit authors",
	bot_author_share: "Share of commits from bot or app accounts",
	workflow_runs: "Automated CI runs observed",
	head_sha: "Commit the reading was taken at"
};
var OP_LABEL = {
	development_initiation: "Development initiation",
	deployment: "Deployment",
	treasury_control: "Treasury control"
};
/** Every limiter the scorer can apply, in the reader's language.
*
* SPEC 3.1 item 3 requires "which limiters were applied". A code alone is a citation to a document
* the reader does not have; an unrecognised code still prints raw rather than being swallowed. */
var LIMITER_TEXT = {
	"O1:mixed_classes->inferred": "evidence of mixed forgery cost, so this level is inferred rather than measured",
	"O2:no_runtime_trace->capped_L2": "no runtime trace, so the level is capped at L2 whatever the repository suggests",
	"O3:contradicts_claim->claim_rejected": "the subject claimed a higher level than the evidence supports; the claim was rejected",
	control_map_cap: "a human control path exists, so the level cannot exceed what the map allows"
};
var OP_DESC = {
	development_initiation: "Who starts and lands changes to the running system, and whether that requires a human.",
	deployment: "Who ships a change to production, and whether a human approves each one.",
	treasury_control: "Who can move funds, change destinations, or alter spending rules."
};
/** One accountability field.
*
* Three renderings for three states, because there are three. A measured absence says who looked;
* an unmeasured field says nobody did and why. Under schema 1.0.0 this component had to guess,
* and guessed differently in adjacent rows - which is what exposed the schema defect. */
function AccFact({ f, yes, no }) {
	if (!f.measured) return /* @__PURE__ */ jsx(AbsentMark, { reason: f.reason });
	const register = f.confidence === "assumed" ? /* @__PURE__ */ jsx("span", {
		className: "evidence-class ml-2",
		title: "Taken from the subject's own declaration; not independently verified.",
		children: "self-declared"
	}) : f.confidence ? /* @__PURE__ */ jsx("span", {
		className: "evidence-class ml-2",
		children: f.confidence
	}) : null;
	if (f.value === null) return /* @__PURE__ */ jsxs("span", {
		className: "text-[var(--color-ink-2)]",
		children: [
			no ?? "none",
			" — stated, not omitted",
			register
		]
	});
	return /* @__PURE__ */ jsxs("span", { children: [f.value === true ? yes ?? "present" : String(f.value), register] });
}
function Passport({ p }) {
	const v = p.verified;
	const affiliated = p.verifier_affiliation === "same_owner";
	const unmeasured = v.operations.filter((o) => !o.measured).length;
	return /* @__PURE__ */ jsxs(Page, { children: [
		/* @__PURE__ */ jsxs("nav", {
			className: "text-xs text-[var(--color-ink-3)] mb-3",
			children: [
				/* @__PURE__ */ jsx("a", {
					href: "/registry/",
					className: "text-[var(--color-accent)] hover:underline",
					children: "Registry"
				}),
				/* @__PURE__ */ jsx("span", {
					className: "mx-1.5",
					children: "›"
				}),
				/* @__PURE__ */ jsx("span", { children: p.subject_id })
			]
		}),
		/* @__PURE__ */ jsx("h1", {
			className: "text-2xl font-semibold tracking-tight break-all",
			children: p.subject_id
		}),
		/* @__PURE__ */ jsxs("p", {
			className: "mt-1.5 text-xs text-[var(--color-ink-3)]",
			children: [
				"Issued ",
				p.issued_at.slice(0, 19).replace("T", " "),
				" UTC \xA0|\xA0 valid until",
				" ",
				p.valid_until.slice(0, 10),
				daysUntil(p.valid_until) > 0 && /* @__PURE__ */ jsxs("span", {
					className: "text-[var(--color-ink-3)]",
					children: [
						" (",
						daysUntil(p.valid_until),
						" days)"
					]
				}),
				" \xA0|\xA0 protocol ",
				p.provenance.protocol_version,
				" ",
				"\xA0|\xA0 profile ",
				p.provenance.profile_version,
				" \xA0|\xA0 evidence window",
				" ",
				p.provenance.evidence_window_days,
				" days"
			]
		}),
		/* @__PURE__ */ jsxs("p", {
			className: "mt-3 text-sm",
			children: [
				/* @__PURE__ */ jsxs("span", {
					className: "evidence-class",
					title: p.binding_strength === "strong" ? "The identity is bound by something that cannot be quietly reassigned." : "A domain expires and can be resold; a signing key rotates.",
					children: [p.binding_strength, " identity binding"]
				}),
				/* @__PURE__ */ jsx("span", {
					className: "mx-2 text-[var(--color-line-2)]",
					children: "·"
				}),
				/* @__PURE__ */ jsx("span", {
					className: "evidence-class",
					children: effectiveStatus(p.status, p.valid_until)
				}),
				/* @__PURE__ */ jsx("span", {
					className: "mx-2 text-[var(--color-line-2)]",
					children: "·"
				}),
				/* @__PURE__ */ jsxs("strong", {
					className: "font-medium",
					children: [
						v.operations.length - unmeasured,
						" of ",
						v.operations.length,
						" operations measured."
					]
				}),
				" ",
				/* @__PURE__ */ jsx("span", {
					className: "text-[var(--color-ink-2)]",
					children: unmeasured === 0 ? "Every operation on this subject carries evidence." : "The rest are stated as unmeasured, with the reason, rather than scored as zero."
				})
			]
		}),
		effectiveStatus(p.status, p.valid_until) === "stale" && /* @__PURE__ */ jsx("div", {
			className: "mt-3",
			children: /* @__PURE__ */ jsxs(Strip, {
				tone: "warn",
				children: [
					/* @__PURE__ */ jsx("strong", { children: "This passport has lapsed." }),
					" Its evidence window closed on",
					" ",
					p.valid_until.slice(0, 10),
					" and it has not been renewed. Nothing below is retracted — it was true when measured — but a verdict has a shelf life, and a reader deciding today should know they are reading a record rather than a current statement."
				]
			})
		}),
		v.projection === null && v.projection_absent_reason === "unreadable" && /* @__PURE__ */ jsx("div", {
			className: "mt-3",
			children: /* @__PURE__ */ jsxs(Strip, {
				tone: "info",
				children: [/* @__PURE__ */ jsx("strong", { children: "This subject has not presented itself publicly." }), " The repository does not answer a reader holding no credential, so nothing here could be measured. We hold a credential that would read it — and deliberately did not use one, because evidence only we can reach is not evidence anyone else can recompute, and a verdict nobody can check is worth nothing. This record stays as it is until the subject opens the source or offers a channel that anyone could use."]
			})
		}),
		affiliated && /* @__PURE__ */ jsx("div", {
			className: "mt-3",
			children: /* @__PURE__ */ jsxs(Strip, {
				tone: "warn",
				children: [/* @__PURE__ */ jsx("strong", { children: "Affiliated verification." }), " The subject and the verifier’s owner are the same party. This record is a rehearsal of the protocol, not an independent verification, and it is marked so rather than left to be assumed."]
			})
		}),
		/* @__PURE__ */ jsx("section", {
			className: "mt-6 bg-[var(--color-paper)] border border-[var(--color-line)]",
			children: /* @__PURE__ */ jsxs("div", {
				className: "grid gap-6 p-5 md:grid-cols-[minmax(14rem,18rem)_1fr]",
				children: [/* @__PURE__ */ jsxs("div", { children: [
					/* @__PURE__ */ jsx("h2", {
						className: "text-xs uppercase tracking-wide text-[var(--color-ink-2)]",
						children: "Autonomy projection"
					}),
					/* @__PURE__ */ jsx("div", {
						className: "mt-2",
						children: /* @__PURE__ */ jsx(Projection, {
							value: v.projection,
							absentReason: v.projection_absent_reason
						})
					}),
					/* @__PURE__ */ jsxs("p", {
						className: "mt-3 text-xs leading-relaxed text-[var(--color-ink-2)] border-l-2 border-[var(--color-line-2)] pl-3",
						children: [
							"Measures ",
							/* @__PURE__ */ jsx("strong", { children: "autonomy" }),
							". Not reliability, not decision quality, not profitability, and not the presence of an accountable party."
						]
					})
				] }), /* @__PURE__ */ jsxs("div", { children: [
					/* @__PURE__ */ jsx("h2", {
						className: "text-xs uppercase tracking-wide text-[var(--color-ink-2)]",
						children: "Per operation"
					}),
					/* @__PURE__ */ jsx("p", {
						className: "mt-1 text-xs text-[var(--color-ink-3)]",
						children: "A level is assigned to an operation, never to a company. A single number for a whole company is a marketing number."
					}),
					/* @__PURE__ */ jsx("ul", {
						className: "mt-3 divide-y divide-[var(--color-line)] border-t border-[var(--color-line)]",
						children: v.operations.map((o) => /* @__PURE__ */ jsxs("li", {
							className: "flex gap-4 py-3",
							children: [/* @__PURE__ */ jsx(LevelRail, {
								level: o.level,
								measured: o.measured
							}), /* @__PURE__ */ jsxs("div", {
								className: "min-w-0",
								children: [
									/* @__PURE__ */ jsxs("div", {
										className: "flex flex-wrap items-baseline gap-2",
										children: [
											/* @__PURE__ */ jsx("span", {
												className: "font-medium",
												children: OP_LABEL[o.operation] ?? o.operation
											}),
											o.measured && o.confidence === "inferred" && /* @__PURE__ */ jsx("span", {
												className: "evidence-class",
												title: "",
												children: "inferred"
											}),
											!o.measured && /* @__PURE__ */ jsx(AbsentMark, { reason: o.level })
										]
									}),
									/* @__PURE__ */ jsx("p", {
										className: "mt-0.5 text-sm text-[var(--color-ink-2)]",
										children: OP_DESC[o.operation] ?? ""
									}),
									o.limiters_applied.length > 0 && /* @__PURE__ */ jsx("ul", {
										className: "mt-1.5 space-y-0.5",
										children: o.limiters_applied.map((lim) => /* @__PURE__ */ jsxs("li", {
											className: "text-xs text-[var(--color-ink-3)]",
											children: [
												/* @__PURE__ */ jsx("span", {
													className: "font-mono",
													children: lim.split(":")[0]
												}),
												" ",
												LIMITER_TEXT[lim] ?? lim
											]
										}, lim))
									})
								]
							})]
						}, o.operation))
					}),
					unmeasured > 0 && /* @__PURE__ */ jsxs("p", {
						className: "mt-3 text-xs text-[var(--color-ink-3)]",
						children: [
							unmeasured,
							" of ",
							v.operations.length,
							" operations are not measured. Runtime evidence is not collected at this stage, and the passport says so rather than scoring them zero."
						]
					})
				] })]
			})
		}),
		/* @__PURE__ */ jsxs("section", {
			className: "mt-6",
			children: [
				/* @__PURE__ */ jsx("h2", {
					className: "text-sm font-semibold",
					children: "Accountability"
				}),
				/* @__PURE__ */ jsxs("p", {
					className: "mt-1 text-xs text-[var(--color-ink-3)] max-w-[46rem]",
					children: ["Deliberately outside the score. The ladder measures how little a human is required; it says nothing about who answers when something goes wrong, so an empty control map can yield maximum autonomy and no addressee at once — both truths side by side.", Object.values(p.accountability).every((f) => !f.measured) && /* @__PURE__ */ jsxs(Fragment, { children: [" ", /* @__PURE__ */ jsx("em", { children: "Nothing here has been inspected yet. That is why every row reads not measured rather than none: a field nobody looked at is not a business without an answer." })] })]
				}),
				/* @__PURE__ */ jsx("div", {
					className: "mt-3 bg-[var(--color-paper)] border border-[var(--color-line)] px-5 py-1",
					children: /* @__PURE__ */ jsx(Facts, { rows: [
						["Emergency stop", /* @__PURE__ */ jsx(AccFact, {
							f: p.accountability.emergency_stop,
							yes: "present",
							no: "none"
						})],
						["Claims addressee", /* @__PURE__ */ jsx(AccFact, { f: p.accountability.claims_addressee })],
						["Insurance", /* @__PURE__ */ jsx(AccFact, { f: p.accountability.insurance })],
						["Dispute path", /* @__PURE__ */ jsx(AccFact, { f: p.accountability.dispute_path })]
					] })
				})
			]
		}),
		Object.keys(v.observations || {}).length > 0 && /* @__PURE__ */ jsxs("section", {
			className: "mt-6",
			children: [
				/* @__PURE__ */ jsx("h2", {
					className: "text-sm font-semibold",
					children: "What was actually observed"
				}),
				/* @__PURE__ */ jsx("p", {
					className: "mt-1 text-xs text-[var(--color-ink-3)] max-w-[46rem]",
					children: "The quantities the level above was computed from. They are published so the verdict can be recomputed rather than believed — and so a reader who disagrees with the reasoning can say where."
				}),
				/* @__PURE__ */ jsx("div", {
					className: "mt-3 bg-[var(--color-paper)] border border-[var(--color-line)] px-5 py-1",
					children: /* @__PURE__ */ jsx(Facts, { rows: Object.entries(v.observations).map(([key, o]) => [OBS_LABEL[key] ?? key, typeof o === "string" || o === null ? /* @__PURE__ */ jsx("span", {
						className: "font-mono text-xs",
						children: o ?? "—"
					}) : o.measured ? /* @__PURE__ */ jsx("span", {
						className: "tabular-nums",
						children: o.value
					}) : /* @__PURE__ */ jsx(AbsentMark, { reason: o.absent_reason })]) })
				})
			]
		}),
		/* @__PURE__ */ jsxs("section", {
			className: "mt-6",
			children: [/* @__PURE__ */ jsx("h2", {
				className: "text-sm font-semibold",
				children: "Identity binding"
			}), /* @__PURE__ */ jsx("div", {
				className: "mt-3 bg-[var(--color-paper)] border border-[var(--color-line)] px-5 py-1",
				children: /* @__PURE__ */ jsx(Facts, { rows: [
					["Binding", /* @__PURE__ */ jsx("code", {
						className: "font-mono text-xs",
						children: p.subject_id
					})],
					["Strength", p.binding_strength === "strong" ? /* @__PURE__ */ jsx("span", {
						style: { color: "var(--color-pass)" },
						children: "strong"
					}) : /* @__PURE__ */ jsx("span", {
						style: { color: "var(--color-warn)" },
						children: "weak"
					})],
					["Properties", p.binding_flags.join(", ") || "—"],
					["Why it matters", /* @__PURE__ */ jsx("span", {
						className: "text-[var(--color-ink-2)]",
						children: "A domain expires and can be resold; a signing key rotates. Equating either with ownership of a token would overstate what the binding guarantees."
					})]
				] })
			})]
		}),
		/* @__PURE__ */ jsxs("section", {
			className: "mt-6",
			children: [
				/* @__PURE__ */ jsx("h2", {
					className: "text-sm font-semibold",
					children: "Human control map — coverage"
				}),
				/* @__PURE__ */ jsxs("p", {
					className: "mt-1 text-xs text-[var(--color-ink-3)] max-w-[46rem]",
					children: [
						"This map can prove that a control path ",
						/* @__PURE__ */ jsx("em", { children: "exists" }),
						". It can never prove that no undiscovered path exists — that is impossible in principle, so the map publishes what it inspected and what it could not reach."
					]
				}),
				/* @__PURE__ */ jsx("div", {
					className: "mt-3 bg-[var(--color-paper)] border border-[var(--color-line)] px-5 py-1",
					children: /* @__PURE__ */ jsx(Facts, { rows: [
						["Inspected", v.coverage.inspected.join(", ") || "—"],
						["Out of reach", Object.entries(v.coverage.out_of_reach).length === 0 ? "—" : /* @__PURE__ */ jsx("ul", {
							className: "space-y-0.5",
							children: Object.entries(v.coverage.out_of_reach).map(([k, why]) => /* @__PURE__ */ jsxs("li", { children: [/* @__PURE__ */ jsx("span", {
								className: "font-mono text-xs",
								children: k
							}), /* @__PURE__ */ jsxs("span", {
								className: "text-[var(--color-ink-3)]",
								children: [" — ", why]
							})] }, k))
						})],
						["An undiscovered path would look like", /* @__PURE__ */ jsx("span", {
							className: "text-[var(--color-ink-2)]",
							children: v.coverage.unknown_shape
						})],
						["Level ceiling implied by the map", v.control_map_cap === null ? /* @__PURE__ */ jsx(AbsentMark, { reason: null }) : `L${v.control_map_cap}`]
					] })
				})
			]
		}),
		/* @__PURE__ */ jsxs("section", {
			className: "mt-6",
			children: [/* @__PURE__ */ jsxs("h2", {
				className: "text-sm font-semibold",
				children: ["Self-reported ", /* @__PURE__ */ jsx("span", {
					className: "font-normal text-[var(--color-ink-3)]",
					children: "— claimed by the subject, not verified by us"
				})]
			}), /* @__PURE__ */ jsx("div", {
				className: "mt-3 border border-dashed border-[var(--color-line-2)] bg-[var(--color-paper-2)] px-5 py-1",
				children: /* @__PURE__ */ jsx(Facts, { rows: Object.entries(p.self_reported).map(([k, val]) => [k, String(val)]) })
			})]
		})
	] });
}
//#endregion
//#region src/pages/Apply.tsx
/** Intake. What we may touch is stated on the form, not in terms of service - because it is the
* thing that decides whether we may reach a live system at all.
*
* THE CHOICE IS BACK, AND IT IS NARROWER THAN THE ONE THAT WAS REMOVED (D-23). It was withdrawn on
* 2026-08-20 (D-21) because no prober existed, and offering it would have asked a stranger to grant
* access to a live system that nothing here could use. T-2.12 built the prober, and it does exactly
* one thing: an unauthenticated access attempt against a path the subject says is closed. So the
* option names that one thing rather than "active probing" in general - the artefact is one action
* wide and the offer may not be wider.
*
* AND THE OPTION ASKS RATHER THAN GRANTS. `src/mandate/mandate.py` opens "a mandate is a legal
* object, not a checkbox": it has to state permitted actions, their limits, what must not be
* affected, liability, an abort condition and how it is revoked. A radio button collects none of
* that, so what this control records is a REQUEST, and the endpoint stores it beside the policy
* actually applied, which stays `passive` for every submission (`mandate_requested` /
* `mandate_applied`). A form that appeared to grant a probing mandate would be the same claim
* outrunning its artefact one floor down from the one D-21 removed.
*
* THIS FORM USED TO DO NOTHING. `onSubmit` was `preventDefault` and nothing else: zero requests,
* no confirmation, no error. It is the only action the site asks for, reached from the primary
* call to action and from a button in the masthead on every screen, and a visitor who filled it in
* correctly received silence.
*
* What the confirmation may claim is a substantive question, not a wording one (Fable's ruling).
* "Received" asserts that somebody has taken responsibility for reading it, and that is only true
* because the submission is written durably AND announced in a channel the operator actually
* watches. When the announcement fails, the record still exists and the page says so in different
* words rather than claiming the stronger thing. And nothing here promises a clock: no side of
* this has committed to one, so the page may not invent it. */
var ISSUES = "https://github.com/whiteknightonhorse/provek/issues";
var DECISION_LOG = "https://github.com/whiteknightonhorse/provek/blob/main/DECISIONS.md#d-14-measurement-on-the-public-surface-ga4-without-a-consent-banner";
function Apply() {
	const [sent, setSent] = useState({ state: "idle" });
	async function submit(e) {
		e.preventDefault();
		const form = new FormData(e.currentTarget);
		const asked = form.get("mandate") === "active" ? "active" : "passive";
		setSent({ state: "sending" });
		try {
			const r = await fetch("/api/apply", {
				method: "POST",
				headers: { "content-type": "application/json" },
				body: JSON.stringify({
					repo: form.get("repo"),
					contact: form.get("contact"),
					mandate: asked,
					website: form.get("website")
				})
			});
			const d = await r.json().catch(() => ({}));
			if (!r.ok || !d.ok) {
				setSent({
					state: "failed",
					why: d.error || `HTTP ${r.status}`
				});
				return;
			}
			setSent({
				state: "sent",
				delivered: Boolean(d.delivered),
				asked
			});
		} catch (err) {
			setSent({
				state: "failed",
				why: err.message
			});
		}
	}
	if (sent.state === "sent") return /* @__PURE__ */ jsx(Page, { children: /* @__PURE__ */ jsxs("div", {
		className: "max-w-[40rem]",
		children: [
			/* @__PURE__ */ jsx("h1", {
				className: "text-2xl font-semibold tracking-tight",
				children: "Request recorded"
			}),
			/* @__PURE__ */ jsx("div", {
				className: "mt-4",
				children: /* @__PURE__ */ jsx(Strip, {
					tone: "pass",
					children: sent.delivered ? /* @__PURE__ */ jsxs(Fragment, { children: [/* @__PURE__ */ jsx("strong", { children: "Your request is recorded and the notification to the operator went out." }), " Nothing further is required from you."] }) : /* @__PURE__ */ jsxs(Fragment, { children: [/* @__PURE__ */ jsx("strong", { children: "Your request is recorded." }), " The notification to the operator did not go through, so it may be read later than usual. The record itself is safe - we are telling you this rather than claiming otherwise."] })
				})
			}),
			/* @__PURE__ */ jsx("p", {
				className: "mt-5 text-sm text-[var(--color-ink-2)]",
				children: "Verification runs are performed by hand at this stage. If yours runs, the passport appears in the registry and you are contacted at the address you gave. There is no queue position and no promised date, because nothing here has promised one."
			}),
			sent.asked === "active" && /* @__PURE__ */ jsxs("p", {
				className: "mt-4 text-sm text-[var(--color-ink-2)]",
				children: [/* @__PURE__ */ jsx("strong", { children: "You asked about an active-probing mandate." }), " Nothing is authorised by this form and nothing will be sent at your systems. What happens next is that the operator writes to you with a document to agree: it names the one action, the paths, a ceiling on how often, what must not be affected, who answers for damage, what stops the run, and how you revoke it. No request runs before you have signed it."]
			}),
			/* @__PURE__ */ jsxs("p", {
				className: "mt-4 text-sm",
				children: [
					/* @__PURE__ */ jsx("a", {
						href: "/registry/",
						className: "text-[var(--color-accent)] hover:underline",
						children: "See the registry"
					}),
					" ",
					/* @__PURE__ */ jsx("span", {
						className: "text-[var(--color-ink-3)]",
						children: "— every record it holds, and what each one could not measure."
					})
				]
			})
		]
	}) });
	return /* @__PURE__ */ jsx(Page, { children: /* @__PURE__ */ jsxs("div", {
		className: "max-w-[40rem]",
		children: [
			/* @__PURE__ */ jsx("h1", {
				className: "text-2xl font-semibold tracking-tight",
				children: "Request verification"
			}),
			/* @__PURE__ */ jsx("p", {
				className: "mt-2 text-sm text-[var(--color-ink-2)]",
				children: "Free at this stage. We verify only what you ask us to verify, and only what you give us access to."
			}),
			sent.state === "failed" && /* @__PURE__ */ jsx("div", {
				className: "mt-4",
				children: /* @__PURE__ */ jsxs(Strip, {
					tone: "warn",
					children: [
						/* @__PURE__ */ jsx("strong", { children: "Not recorded." }),
						" ",
						sent.why,
						". Nothing was saved, so please try again - and if it keeps failing, the one channel that certainly works is",
						" ",
						/* @__PURE__ */ jsx("a", {
							href: ISSUES,
							className: "text-[var(--color-accent)] hover:underline",
							children: "an issue on the repository"
						}),
						"."
					]
				})
			}),
			/* @__PURE__ */ jsxs("form", {
				className: "mt-7 space-y-5",
				onSubmit: submit,
				children: [
					/* @__PURE__ */ jsxs("div", {
						className: "sr-only",
						"aria-hidden": "true",
						children: [/* @__PURE__ */ jsx("label", {
							htmlFor: "website",
							children: "Leave this empty"
						}), /* @__PURE__ */ jsx("input", {
							id: "website",
							name: "website",
							type: "text",
							tabIndex: -1,
							autoComplete: "off"
						})]
					}),
					/* @__PURE__ */ jsxs("div", { children: [
						/* @__PURE__ */ jsx("label", {
							htmlFor: "repo",
							className: "block text-sm font-medium",
							children: "Repository URL"
						}),
						/* @__PURE__ */ jsx("p", {
							className: "mt-0.5 text-xs text-[var(--color-ink-3)]",
							children: "Public repositories only at this stage. That restriction exists so we never hold your secrets — and so that anyone can recompute the verdict from the same source."
						}),
						/* @__PURE__ */ jsx("input", {
							id: "repo",
							name: "repo",
							type: "url",
							required: true,
							placeholder: "https://github.com/org/repo",
							className: "mt-2 w-full border border-[var(--color-line-2)] bg-[var(--color-paper)] px-3 py-2 text-base"
						})
					] }),
					/* @__PURE__ */ jsxs("div", { children: [/* @__PURE__ */ jsx("label", {
						htmlFor: "contact",
						className: "block text-sm font-medium",
						children: "Contact"
					}), /* @__PURE__ */ jsx("input", {
						id: "contact",
						name: "contact",
						type: "email",
						required: true,
						placeholder: "you@example.com",
						className: "mt-2 w-full border border-[var(--color-line-2)] bg-[var(--color-paper)] px-3 py-2 text-base"
					})] }),
					/* @__PURE__ */ jsxs("fieldset", {
						className: "border border-[var(--color-line-2)] bg-[var(--color-paper)] p-3",
						children: [
							/* @__PURE__ */ jsx("legend", {
								className: "px-1 text-sm font-medium",
								children: "What we may touch"
							}),
							/* @__PURE__ */ jsxs("p", {
								className: "text-xs text-[var(--color-ink-3)]",
								children: [
									/* @__PURE__ */ jsx("strong", {
										className: "text-[var(--color-ink-2)]",
										children: "Without a mandate we do not touch production."
									}),
									" ",
									"Whichever you choose, this form authorises nothing on its own."
								]
							}),
							/* @__PURE__ */ jsxs("label", {
								className: "mt-3 flex gap-2.5",
								children: [/* @__PURE__ */ jsx("input", {
									type: "radio",
									name: "mandate",
									value: "passive",
									defaultChecked: true,
									className: "mt-1"
								}), /* @__PURE__ */ jsxs("span", {
									className: "text-sm",
									children: [/* @__PURE__ */ jsx("strong", { children: "Read-only verification." }), /* @__PURE__ */ jsx("span", {
										className: "block text-xs text-[var(--color-ink-3)]",
										children: "We read what is already public and touch nothing you run. Fewer operations can be measured that way, and the passport says which ones and why."
									})]
								})]
							}),
							/* @__PURE__ */ jsxs("label", {
								className: "mt-3 flex gap-2.5",
								children: [/* @__PURE__ */ jsx("input", {
									type: "radio",
									name: "mandate",
									value: "active",
									className: "mt-1"
								}), /* @__PURE__ */ jsxs("span", {
									className: "text-sm",
									children: [/* @__PURE__ */ jsx("strong", { children: "Ask about an active-probing mandate as well." }), /* @__PURE__ */ jsx("span", {
										className: "block text-xs text-[var(--color-ink-3)]",
										children: "One operation exists today: we attempt to use a path you tell us is closed, and report whether your running system actually refuses it — which your repository cannot show. Ticking this records the question. It is answered with a document naming the action, the paths, a ceiling on how often, what must not be affected, who answers for damage, what stops the run and how you revoke it, and nothing is sent at your systems before you sign it."
									})]
								})]
							})
						]
					}),
					/* @__PURE__ */ jsx("button", {
						type: "submit",
						disabled: sent.state === "sending",
						className: "border border-[var(--color-ink)] bg-[var(--color-ink)] text-[var(--color-paper)] px-4 py-2 text-sm disabled:opacity-60",
						children: sent.state === "sending" ? "Sending…" : "Submit request"
					}),
					/* @__PURE__ */ jsx("p", {
						className: "text-xs text-[var(--color-ink-3)]",
						children: "Nothing is charged. There is no payment step anywhere on this site, in this phase or any later one — money does not pass through us by design."
					}),
					/* @__PURE__ */ jsxs("div", {
						className: "border-t border-[var(--color-line)] pt-4",
						children: [/* @__PURE__ */ jsx("h2", {
							className: "text-sm font-medium",
							children: "What happens to what you type here"
						}), /* @__PURE__ */ jsxs("ul", {
							className: "mt-2 space-y-1 text-xs text-[var(--color-ink-3)]",
							children: [
								/* @__PURE__ */ jsxs("li", { children: [/* @__PURE__ */ jsx("strong", {
									className: "text-[var(--color-ink-2)]",
									children: "Stored:"
								}), " the repository URL, your address, the time, and the two-letter country your request arrived from — plus four fields about the record rather than about you: a random identifier, which mandate you asked for, which one we applied (always the read-only one), and whether our notification to the operator went through. Nothing further, and this form sets no cookie of its own."] }),
								/* @__PURE__ */ jsxs("li", { children: [/* @__PURE__ */ jsx("strong", {
									className: "text-[var(--color-ink-2)]",
									children: "Where:"
								}), " Cloudflare key-value storage, plus — when that notification succeeds — a copy carried by Telegram to the operator’s private channel so a human sees it. Telegram is named because a message channel that reaches a person passes through somebody; the stored record is read by the operator alone."] }),
								/* @__PURE__ */ jsxs("li", { children: [/* @__PURE__ */ jsx("strong", {
									className: "text-[var(--color-ink-2)]",
									children: "Used for:"
								}), " deciding whether to run a verification and contacting you about it. Never for anything else, never sold, never passed on."] }),
								/* @__PURE__ */ jsxs("li", { children: [/* @__PURE__ */ jsx("strong", {
									className: "text-[var(--color-ink-2)]",
									children: "Deleted:"
								}), " whenever you ask, by opening an issue or replying to any message from us — the stored record and the message-channel copy together, both by hand, since nothing here deletes on a timer. There is nothing to unsubscribe from — we do not send anything you did not ask for."] }),
								/* @__PURE__ */ jsxs("li", { children: [
									/* @__PURE__ */ jsx("strong", {
										className: "text-[var(--color-ink-2)]",
										children: "Separately, about this whole site:"
									}),
									" ",
									"Google Analytics runs on every page here, without a consent banner. It sets a cookie and creates an identifier for your browser, and what it records goes to Google. That is the operator’s decision and it is written down, with the argument against it, in the",
									" ",
									/* @__PURE__ */ jsx("a", {
										href: DECISION_LOG,
										className: "text-[var(--color-accent)] hover:underline",
										children: "project’s decision log"
									}),
									". Advertising and personalisation signals are switched off, which is the most that can be said for it."
								] })
							]
						})]
					})
				]
			})
		]
	}) });
}
//#endregion
//#region src/pages/Method.tsx
/** The methodology is published in full - it is an asset, not a vulnerability (decision A-8).
* Publishing it invites optimisation against it, which is the price of being reproducible. */
var LADDER = [
	["L0", "A human performs the operation; the agent drafts or advises."],
	["L1", "The agent performs it; a human approves each instance."],
	["L2", "The agent performs it; a human approves by exception."],
	["L3", "The agent performs and decides; a human may intervene but routinely does not."],
	["L4", "Intervention requires a privileged path, and that path is recorded."],
	["L5", "No human control path exists for this operation."]
];
function Method() {
	return /* @__PURE__ */ jsx(Page, { children: /* @__PURE__ */ jsxs("div", {
		className: "max-w-[46rem]",
		children: [
			/* @__PURE__ */ jsx("h1", {
				className: "text-2xl font-semibold tracking-tight",
				children: "Method"
			}),
			/* @__PURE__ */ jsx("p", {
				className: "mt-2 text-sm text-[var(--color-ink-2)]",
				children: "Published in full. A verdict that only we can reproduce would be a brand, not a standard."
			}),
			/* @__PURE__ */ jsx("div", {
				className: "mt-5",
				children: /* @__PURE__ */ jsxs(Strip, {
					tone: "info",
					children: [
						/* @__PURE__ */ jsx("strong", { children: "Everything here is open, including our own workings." }),
						" The methodology, the scorer, every gate and every decision live at",
						" ",
						/* @__PURE__ */ jsx("a", {
							href: "https://github.com/whiteknightonhorse/provek",
							className: "text-[var(--color-accent)] hover:underline",
							children: "github.com/whiteknightonhorse/provek"
						}),
						", licensed for reuse, so any verdict can be recomputed from the same inputs. The operating documents that produced this instrument are recorded separately at",
						" ",
						/* @__PURE__ */ jsx("a", {
							href: "https://github.com/whiteknightonhorse/provek-method",
							className: "text-[var(--color-accent)] hover:underline",
							children: "provek-method"
						}),
						" ",
						"— provenance, not instruction. Following them has no effect on any verdict: the score is computed from measured operations, and the use of a method is not one of them."
					]
				})
			}),
			/* @__PURE__ */ jsx("h2", {
				className: "mt-8 text-lg font-semibold",
				children: "The ladder"
			}),
			/* @__PURE__ */ jsx("p", {
				className: "mt-1 text-sm text-[var(--color-ink-2)]",
				children: "Assigned per operation, never to a company as a whole. A company can be L4 in deployment and L0 in pricing."
			}),
			/* @__PURE__ */ jsx("div", {
				className: "mt-3 bg-[var(--color-paper)] border border-[var(--color-line)] px-5 py-1",
				children: /* @__PURE__ */ jsx(Facts, { rows: LADDER })
			}),
			/* @__PURE__ */ jsx("h2", {
				className: "mt-8 text-lg font-semibold",
				children: "What it does not measure"
			}),
			/* @__PURE__ */ jsxs("ul", {
				className: "mt-2 text-sm text-[var(--color-ink-2)] list-disc pl-5 space-y-1",
				children: [
					/* @__PURE__ */ jsx("li", { children: "decision quality" }),
					/* @__PURE__ */ jsx("li", { children: "profitability" }),
					/* @__PURE__ */ jsx("li", { children: "whether the autonomy is desirable" }),
					/* @__PURE__ */ jsx("li", { children: "reliability, and whether anyone is accountable" })
				]
			}),
			/* @__PURE__ */ jsx("h2", {
				className: "mt-8 text-lg font-semibold",
				children: "Evidence classes"
			}),
			/* @__PURE__ */ jsx("p", {
				className: "mt-1 text-sm text-[var(--color-ink-2)]",
				children: "Every piece of evidence carries the cost of forging it. Mixing classes inside one number without disclosing the mix is forbidden — otherwise a score would say the same thing about a self-report as about a cryptographic signature."
			}),
			/* @__PURE__ */ jsx("div", {
				className: "mt-3 bg-[var(--color-paper)] border border-[var(--color-line)] px-5 py-1",
				children: /* @__PURE__ */ jsx(Facts, { rows: [
					["self_reported", "the subject, for free — never enters the score"],
					["platform_observed", "the subject, at the cost of sustained theatre"],
					["third_party_attested", "requires collusion with a third party"],
					["cryptographically_bound", "requires compromising a key"]
				] })
			}),
			/* @__PURE__ */ jsx("h2", {
				className: "mt-8 text-lg font-semibold",
				children: "Not measured is a state, not a zero"
			}),
			/* @__PURE__ */ jsx("p", {
				className: "mt-1 text-sm text-[var(--color-ink-2)]",
				children: "Three absences are distinguished and never collapsed: the check ran and nothing qualified; the check did not run; the source could not be read. A missing measurement is not a violation, and a verifier that suspended a subject for its own blindness would be punishing someone for its own failure."
			}),
			/* @__PURE__ */ jsx("h2", {
				className: "mt-8 text-lg font-semibold",
				children: "Notes on the method"
			}),
			/* @__PURE__ */ jsxs("p", {
				className: "mt-1 text-sm text-[var(--color-ink-2)]",
				children: [
					"Parts of the methodology carry more argument than this page has room for, and those are written up separately, one note to a topic. The index lists what has been captured and nothing else, so it is also the record of how much of the method has been written down:",
					" ",
					/* @__PURE__ */ jsx("a", {
						href: "/method/notes/",
						className: "text-[var(--color-accent)] hover:underline",
						children: "notes on the method"
					}),
					"."
				]
			}),
			/* @__PURE__ */ jsx("h2", {
				className: "mt-8 text-lg font-semibold",
				children: "What is specified and not built"
			}),
			/* @__PURE__ */ jsxs("p", {
				className: "mt-1 text-sm text-[var(--color-ink-2)]",
				children: [
					"The specification also defines a second phase, in which a customer commissions work from a verified agent and we witness the fact of performance. None of it is in service and no application for it is being taken. It is written down here anyway, because what a specification forbids us to build is a fact about the product today:",
					" ",
					/* @__PURE__ */ jsx("a", {
						href: "/phase-2/",
						className: "text-[var(--color-accent)] hover:underline",
						children: "phase two, and why it is not running"
					}),
					"."
				]
			})
		]
	}) });
}
//#endregion
//#region src/pages/Phase2.tsx
/** Phase two, announced as SPECIFIED and never as available.
*
* WHY THIS PAGE IS ALLOWED TO EXIST, AND WHAT IT MAY NOT BECOME. D-05 reserves space for phase 2
* in the layout and forbids announcing a feature that does not exist. That boundary still holds
* everywhere it was drawn: the registry's trailing column is still empty, the passport's task
* history is still absent, the corpus nav slot is still disabled. What changed is narrower, and it
* is recorded as D-16: the phase is DESCRIBED once, on a page of its own, because a specification
* that constrains what we may build is a fact about the product today, whereas a "commission work"
* control on a registry row would be an offer.
*
* The difference between a description and an offer has to survive a screenshot, because a
* screenshot is how this page will be quoted. Hence the refusal at the top, the refusal at the
* bottom, no control anywhere on the page that could be pressed, and no date anywhere in it.
*
* Every statement here is taken from SPEC.md section 4.1, "Phase 2 - what it is, and what it is
* not", which in turn takes it from the project specification. Nothing is added. This is the one
* page where an invented capability would be indistinguishable from the marketing this product
* exists to detect, so the rule is stricter here than anywhere else: if a sentence cannot be traced
* to a paragraph, it is not on the page. */
var SPEC = "https://github.com/whiteknightonhorse/provek/blob/main/SPEC.md";
/** From SPEC.md 4.1. `enforced` means the deployed contract carries the constraint out itself;
* `evidenced` means it can be shown and argued and nothing more. Presenting the second as the first
* is forbidden, and the specification puts that obligation on the interface, not only on the schema
* - which is why the status is a column here rather than a sentence somewhere below.
*
* This comment said "makes it impossible" until Fable found it in the source AFTER the same phrase
* had been corrected on the page. SPEC 4.1 now forbids that upgrade in normative terms, and a
* comment contradicting the rule it explains is how the next editor learns which one to believe. */
var CONSTRAINTS = [
	["Ceiling on the amount", "enforced"],
	["Permitted on-chain recipient", "enforced"],
	["Release of a milestone against a machine-checkable criterion", "enforced"],
	["Timeout, and return of whatever was not committed", "enforced"],
	["“The money was spent on compute”", "evidenced"],
	["“The work was done well”", "evidenced"],
	["“The agent did not hand the task to a human”", "evidenced"]
];
/** `rejected` is on the diagram and not only in the sentence about terminal states below it. The
* specification lists it as terminal while showing no arrow that reaches it, which is a small
* version of the defect this whole surface exists to catch: a claim with nothing behind it in the
* artefact. The transition is supplied by the policy gate, which refuses anything missing a
* condition of creation.
*
* The seam that reconstruction leaves, named rather than smoothed over: the specification also says
* such a task "is not created at all", which cannot both be true and leave it sitting in a terminal
* state. The reading taken here - a DRAFT is refused at `policy_check` and never becomes a funded
* task - satisfies both sentences, and it is recorded in SPEC.md 4.1 as a reconstruction rather
* than presented as quotation. The durable fix belongs in the specification, not on this page. */
var LIFECYCLE = [
	"draft → policy_check → funded → executing",
	"policy_check → rejected                     (a condition of creation is missing)",
	"executing → milestone_released → executing  (partial release)",
	"executing → completed                       (every acceptance criterion met)",
	"executing → failed                          (a failure criterion fired)",
	"executing → timed_out                       (the timeout expired — by time, with no event)",
	"failed | timed_out → settled                (the uncommitted remainder returned by code)"
];
function Phase2() {
	return /* @__PURE__ */ jsx(Page, { children: /* @__PURE__ */ jsxs("div", {
		className: "max-w-[46rem]",
		children: [
			/* @__PURE__ */ jsx("h1", {
				className: "text-2xl font-semibold tracking-tight",
				children: "Phase two: funding tasks"
			}),
			/* @__PURE__ */ jsx("p", {
				className: "mt-2 text-sm text-[var(--color-ink-2)]",
				children: "Specified. Not built. Not open. Everything below describes what the specification requires of phase 2 — it is not a description of anything that runs."
			}),
			/* @__PURE__ */ jsxs("div", {
				className: "mt-5 space-y-3",
				children: [/* @__PURE__ */ jsxs(Strip, {
					tone: "warn",
					children: [/* @__PURE__ */ jsx("strong", { children: "Nothing on this page is in service." }), " No funding task can be created, no work can be commissioned through us, and no application for one is being taken. Phase 2 is deferred by decision A-10 — projects first — because a registry is useful without the second side, and the second side is not useful without a registry. Deferred is not cancelled: the specification defines phase 2 so that it will not have to be designed twice."]
				}), /* @__PURE__ */ jsxs(Strip, {
					tone: "info",
					children: [/* @__PURE__ */ jsx("strong", { children: "There is no date here, and there will not be one." }), " Nothing and nobody has committed to a date, so this page may not invent one. A promised date would be exactly the thing this product exists to detect: a claim stronger than the artefact behind it."]
				})]
			}),
			/* @__PURE__ */ jsx("h2", {
				className: "mt-9 text-lg font-semibold",
				children: "Where this sits"
			}),
			/* @__PURE__ */ jsxs("ol", {
				className: "mt-3 space-y-3 text-sm text-[var(--color-ink-2)]",
				children: [
					/* @__PURE__ */ jsxs("li", {
						className: "border-l border-[var(--color-line-2)] pl-3.5",
						children: [/* @__PURE__ */ jsx("strong", {
							className: "text-[var(--color-ink)]",
							children: "You ask to be verified."
						}), " Nobody is assessed who did not ask, and without a mandate nothing in your production is touched. This part is open today."]
					}),
					/* @__PURE__ */ jsxs("li", {
						className: "border-l border-[var(--color-line-2)] pl-3.5",
						children: [
							/* @__PURE__ */ jsx("strong", {
								className: "text-[var(--color-ink)]",
								children: "A passport is issued."
							}),
							" ",
							"Machine-readable first: a level for each business operation, the evidence behind each level, and the reason for every operation that could not be measured. This part is open today."
						]
					}),
					/* @__PURE__ */ jsxs("li", {
						className: "border-l border-[var(--color-line-2)] pl-3.5",
						children: [
							/* @__PURE__ */ jsx("strong", {
								className: "text-[var(--color-ink)]",
								children: "In phase 2, a funding task can be addressed to a subject."
							}),
							" ",
							"A customer commissions work, the agent performs it, and the incubator witnesses the fact of performance. ",
							/* @__PURE__ */ jsx("strong", {
								className: "text-[var(--color-ink)]",
								children: "This part does not exist."
							})
						]
					})
				]
			}),
			/* @__PURE__ */ jsx("p", {
				className: "mt-3 text-sm text-[var(--color-ink-2)]",
				children: "The order is a dependency, not a sales funnel. Phase 2 stands on the registry, which is what decision A-10 means when it says the registry is useful without the second side while the reverse is false."
			}),
			/* @__PURE__ */ jsx("h2", {
				className: "mt-9 text-lg font-semibold",
				children: "What a funding task is, in the specification"
			}),
			/* @__PURE__ */ jsx("div", {
				className: "mt-3 bg-[var(--color-paper)] border border-[var(--color-line)] px-5 py-1",
				children: /* @__PURE__ */ jsx(Facts, { rows: [
					["it is", "a contract for services — procurement"],
					["it is not", "a grant, a donation, a pre-payment for a share, or an investment contract"],
					["the funder", "is a customer, and takes delivery of the result"],
					["a share of revenue", "excluded permanently — not deferred, excluded"],
					["one task, in phase 2.0", "has exactly one principal"]
				] })
			}),
			/* @__PURE__ */ jsxs("p", {
				className: "mt-3 text-sm text-[var(--color-ink-2)]",
				children: [
					"The words ",
					/* @__PURE__ */ jsx("span", {
						className: "font-mono text-xs",
						children: "investment"
					}),
					",",
					" ",
					/* @__PURE__ */ jsx("span", {
						className: "font-mono text-xs",
						children: "investor"
					}),
					",",
					" ",
					/* @__PURE__ */ jsx("span", {
						className: "font-mono text-xs",
						children: "equity"
					}),
					" and",
					" ",
					/* @__PURE__ */ jsx("span", {
						className: "font-mono text-xs",
						children: "secondary market"
					}),
					" are forbidden in the product. The specification records in the same breath that the prohibition is not itself a legal argument: classification follows substance, not vocabulary."
				]
			}),
			/* @__PURE__ */ jsx("h2", {
				className: "mt-9 text-lg font-semibold",
				children: "Money never passes through us"
			}),
			/* @__PURE__ */ jsx("p", {
				className: "mt-2 text-sm text-[var(--color-ink-2)]",
				children: "Decision A-6, and it is permanent rather than deferred — which is why there is no payment step anywhere on this site, not in this phase and not in a later one. We hold and route no funds: no escrow, no treasury, no keys. In phase 2 a customer pays the agent directly. A commission on transfers is excluded forever."
			}),
			/* @__PURE__ */ jsx("p", {
				className: "mt-3 text-sm text-[var(--color-ink-2)]",
				children: "The milestone contract is deployed by the parties themselves. Our part is to publish the template and to hold no key to it. If we deployed that contract and kept an administrative key, the custodial risk decision A-6 removed would return through the back door, and “we are only infrastructure” would stop being true."
			}),
			/* @__PURE__ */ jsx("p", {
				className: "mt-3 text-sm text-[var(--color-ink-2)]",
				children: "What we would be paid for, when it exists, is a fixed fee for the witnessing itself — never a share of what passes between the parties."
			}),
			/* @__PURE__ */ jsx("h2", {
				className: "mt-9 text-lg font-semibold",
				children: "Enforced, or only evidenced — as specified"
			}),
			/* @__PURE__ */ jsxs("p", {
				className: "mt-2 text-sm text-[var(--color-ink-2)]",
				children: [
					"This is the line where products of this kind most often lie, so the specification requires the interface to publish the status of every constraint rather than the constraints alone.",
					" ",
					/* @__PURE__ */ jsx("span", {
						className: "font-mono text-xs",
						children: "enforced"
					}),
					" means the deployed contract carries the constraint out itself. ",
					/* @__PURE__ */ jsx("span", {
						className: "font-mono text-xs",
						children: "evidenced"
					}),
					" means it can be shown and argued, and nothing more. Neither word promises a contract free of defects: the template has not been through the review named at the foot of this page."
				]
			}),
			/* @__PURE__ */ jsx("ul", {
				className: "mt-3 divide-y divide-[var(--color-line)] border-y border-[var(--color-line)]",
				children: CONSTRAINTS.map(([what, status]) => /* @__PURE__ */ jsxs("li", {
					className: "flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 py-2.5",
					children: [/* @__PURE__ */ jsx("span", {
						className: "text-sm",
						children: what
					}), /* @__PURE__ */ jsx("span", {
						className: "shrink-0 font-mono text-xs",
						style: { color: status === "enforced" ? "var(--color-pass)" : "var(--color-warn)" },
						children: status === "enforced" ? "enforced" : "evidenced only"
					})]
				}, what))
			}),
			/* @__PURE__ */ jsxs("p", {
				className: "mt-3 text-sm text-[var(--color-ink-2)]",
				children: [/* @__PURE__ */ jsx("span", {
					className: "font-mono text-xs",
					children: "enforced"
				}), " means enforced by the contract the parties deploy between themselves. Not by us: we are not a party to it."]
			}),
			/* @__PURE__ */ jsx("h2", {
				className: "mt-9 text-lg font-semibold",
				children: "The lifecycle, as specified"
			}),
			/* @__PURE__ */ jsx("div", {
				className: "mt-3 overflow-x-auto bg-[var(--color-paper)] border border-[var(--color-line)] p-4",
				children: /* @__PURE__ */ jsx("pre", {
					className: "font-mono text-xs leading-relaxed whitespace-pre",
					children: LIFECYCLE.join("\n")
				})
			}),
			/* @__PURE__ */ jsxs("p", {
				className: "mt-3 text-sm text-[var(--color-ink-2)]",
				children: [
					"Terminal states are ",
					/* @__PURE__ */ jsx("span", {
						className: "font-mono text-xs",
						children: "completed"
					}),
					",",
					" ",
					/* @__PURE__ */ jsx("span", {
						className: "font-mono text-xs",
						children: "settled"
					}),
					" and",
					" ",
					/* @__PURE__ */ jsx("span", {
						className: "font-mono text-xs",
						children: "rejected"
					}),
					". A funder cannot cancel. The only ways out of ",
					/* @__PURE__ */ jsx("span", {
						className: "font-mono text-xs",
						children: "executing"
					}),
					" are completion, failure and timeout, and all three are performed by the contract rather than decided by a person. An undefined transition is impossible, not undocumented."
				]
			}),
			/* @__PURE__ */ jsxs("p", {
				className: "mt-3 text-sm text-[var(--color-ink-2)]",
				children: [
					"A draft that does not carry acceptance criteria, failure criteria, a timeout, milestones and a ceiling never becomes a task — the policy gate refuses it, and",
					" ",
					/* @__PURE__ */ jsx("span", {
						className: "font-mono text-xs",
						children: "rejected"
					}),
					" is where the refusal lands. That is a condition of creation, not a recommendation. In phase 2.0, financing a task out of the pooled funds of an agent acting for several principals is forbidden, and the check follows the chain from the funder through the delegation to the principal rather than stopping at the funder."
				]
			}),
			/* @__PURE__ */ jsx("h2", {
				className: "mt-9 text-lg font-semibold",
				children: "What is unresolved"
			}),
			/* @__PURE__ */ jsx("p", {
				className: "mt-2 text-sm text-[var(--color-ink-2)]",
				children: "These are on the page because they are unresolved, not in spite of it."
			}),
			/* @__PURE__ */ jsxs("ul", {
				className: "mt-3 space-y-3 text-sm text-[var(--color-ink-2)]",
				children: [
					/* @__PURE__ */ jsxs("li", {
						className: "border-l border-[var(--color-line-2)] pl-3.5",
						children: [
							/* @__PURE__ */ jsx("strong", {
								className: "text-[var(--color-ink)]",
								children: "Only machine-checkable acceptance criteria are admitted."
							}),
							" ",
							"A task whose acceptance is a matter of opinion is never created, which is also the reason we can never be asked to arbitrate one. We would be a witness recording a fact, and an observer holding no money cannot be an arbiter."
						]
					}),
					/* @__PURE__ */ jsxs("li", {
						className: "border-l border-[var(--color-line-2)] pl-3.5",
						children: [/* @__PURE__ */ jsx("strong", {
							className: "text-[var(--color-ink)]",
							children: "Witnessing creates exposure."
						}), " A party relies on our statement at the moment money moves. The specification marks this, and the milestone-contract template, as requiring a lawyer’s review before phase 2 — marked, and not yet resolved."]
					}),
					/* @__PURE__ */ jsxs("li", {
						className: "border-l border-[var(--color-line-2)] pl-3.5",
						children: [
							/* @__PURE__ */ jsx("strong", {
								className: "text-[var(--color-ink)]",
								children: "“The agent did not hand this task to a human” is not verifiable at reasonable cost."
							}),
							" ",
							"It may be published as a probabilistic signal and never as a verdict. That rule is not waiting for phase 2; it binds every signal we publish now."
						]
					})
				]
			}),
			/* @__PURE__ */ jsx("div", {
				className: "mt-9",
				children: /* @__PURE__ */ jsxs(Strip, {
					tone: "info",
					children: [
						/* @__PURE__ */ jsx("strong", { children: "Nothing on this page is an offer." }),
						" The only thing open today is verification, and it is a different thing:",
						" ",
						/* @__PURE__ */ jsx("a", {
							href: "/apply/",
							className: "text-[var(--color-accent)] hover:underline",
							children: "request verification"
						}),
						". To check this page against its source rather than taking it from us, the phase-2 section is in",
						" ",
						/* @__PURE__ */ jsx("a", {
							href: SPEC,
							className: "text-[var(--color-accent)] hover:underline",
							children: "SPEC.md"
						}),
						" ",
						"in the repository."
					]
				})
			})
		]
	}) });
}
//#endregion
//#region src/App.tsx
function Bar({ w, h = "1rem" }) {
	return /* @__PURE__ */ jsx("div", {
		className: "skeleton-bar bg-[var(--color-line)] rounded-sm",
		style: {
			width: w,
			maxWidth: "100%",
			height: h
		}
	});
}
/** Skeletons carry the shape of what is coming, not a generic shimmer. */
function TableSkeleton() {
	return /* @__PURE__ */ jsx(Page, { children: /* @__PURE__ */ jsxs("div", {
		className: "min-h-[100svh]",
		children: [/* @__PURE__ */ jsx(Bar, {
			w: "10rem",
			h: "1.75rem"
		}), /* @__PURE__ */ jsx("div", {
			className: "mt-6 bg-[var(--color-paper)] border border-[var(--color-line)]",
			children: Array.from({ length: 6 }).map((_, i) => /* @__PURE__ */ jsx("div", {
				className: "grid grid-cols-2 sm:grid-cols-5 gap-4 border-b border-[var(--color-line)] px-4 py-3",
				children: Array.from({ length: 5 }).map((__, j) => /* @__PURE__ */ jsx("div", { className: "skeleton-bar h-4 bg-[var(--color-line)] rounded-sm" }, j))
			}, i))
		})]
	}) });
}
function PassportSkeleton() {
	return /* @__PURE__ */ jsx(Page, { children: /* @__PURE__ */ jsxs("div", {
		className: "min-h-[100svh]",
		children: [
			/* @__PURE__ */ jsx(Bar, {
				w: "18rem",
				h: "1.9rem"
			}),
			/* @__PURE__ */ jsx("div", {
				className: "mt-2",
				children: /* @__PURE__ */ jsx(Bar, {
					w: "24rem",
					h: "0.8rem"
				})
			}),
			/* @__PURE__ */ jsx("div", {
				className: "mt-6 bg-[var(--color-paper)] border border-[var(--color-line)] p-5 space-y-5",
				children: Array.from({ length: 4 }).map((_, i) => /* @__PURE__ */ jsxs("div", {
					className: "space-y-2",
					children: [/* @__PURE__ */ jsx(Bar, {
						w: "12rem",
						h: "1rem"
					}), /* @__PURE__ */ jsx(Bar, {
						w: "100%",
						h: "2rem"
					})]
				}, i))
			})
		]
	}) });
}
/** One shape for every dead end, so that the page always names which one it is. */
function DeadEnd({ title, children }) {
	return /* @__PURE__ */ jsxs(Page, { children: [
		/* @__PURE__ */ jsx("h1", {
			className: "text-2xl font-semibold tracking-tight",
			children: title
		}),
		/* @__PURE__ */ jsx("p", {
			className: "mt-2 max-w-[46rem] text-sm text-[var(--color-ink-2)]",
			children
		}),
		/* @__PURE__ */ jsx("p", {
			className: "mt-6 text-sm",
			children: /* @__PURE__ */ jsx("a", {
				href: "/registry/",
				className: "text-[var(--color-accent)] hover:underline",
				children: "Back to the registry"
			})
		})
	] });
}
/** The placeholder route `404.html` is prerendered under.
*
* Cloudflare Pages serves that one document for every address that does not exist, so at build
* time there is no such thing as "the address the reader asked for". Defined here and imported by
* `prerender.mjs` rather than written as a literal in both: a string that means "this is not a real
* route" in two places is a string that will stop meaning it in one of them (L-2). */
var PRERENDER_ROUTE = "/__not_found__/";
var TITLES = {
	"/": "Provek - evidence, not claims",
	"/registry/": "Registry - Provek",
	"/method/": "Method - Provek",
	"/apply/": "Request verification - Provek",
	"/phase-2/": "Phase two: funding tasks, not in service - Provek"
};
/** The one place that decides what a route renders — shared by the browser and by the build-time
* renderer, so a page cannot exist in one and not the other. */
function Body({ route, reg, passport }) {
	if (route.startsWith("/p/")) {
		const p = passport ?? { state: "loading" };
		if (p.state === "ready") return /* @__PURE__ */ jsx(Passport, { p: p.data });
		if (p.state === "missing") return /* @__PURE__ */ jsx(DeadEnd, {
			title: "No passport for this subject",
			children: "Nothing has been issued under this identifier. That is a statement about our registry, not about the subject: an unmeasured business is not a failing one."
		});
		if (p.state === "error") return /* @__PURE__ */ jsxs(DeadEnd, {
			title: "Passport unavailable",
			children: [
				"The record exists in the registry but could not be read (",
				p.why,
				"). This is our failure to serve it, and it says nothing about the subject."
			]
		});
		return /* @__PURE__ */ jsx(PassportSkeleton, {});
	}
	if (route === "/registry/") {
		if (reg.state === "ready") return /* @__PURE__ */ jsx(Registry, { reg: reg.data });
		if (reg.state === "error") return /* @__PURE__ */ jsxs(DeadEnd, {
			title: "Registry unavailable",
			children: [
				"The registry file could not be read (",
				reg.why,
				"). This is our failure to serve it, not a statement about any subject."
			]
		});
		return /* @__PURE__ */ jsx(TableSkeleton, {});
	}
	if (route === "/apply/") return /* @__PURE__ */ jsx(Apply, {});
	if (route === "/method/") return /* @__PURE__ */ jsx(Method, {});
	if (route === "/phase-2/") return /* @__PURE__ */ jsx(Phase2, {});
	if (route === "/") return /* @__PURE__ */ jsx(Landing, { reg: reg.state === "ready" ? reg.data : null });
	return /* @__PURE__ */ jsx(DeadEnd, {
		title: "No such page",
		children: route === "/__not_found__/" ? "Nothing is served at this address." : /* @__PURE__ */ jsxs(Fragment, { children: [
			"Nothing is served at ",
			/* @__PURE__ */ jsx("code", {
				className: "font-mono text-xs",
				children: route
			}),
			"."
		] })
	});
}
function Shell({ route, children, containerRef }) {
	return /* @__PURE__ */ jsxs("div", {
		className: "min-h-screen flex flex-col",
		children: [
			/* @__PURE__ */ jsx("a", {
				href: "#main",
				className: "sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-10 focus:bg-[var(--color-paper)] focus:border focus:border-[var(--color-line-2)] focus:px-3 focus:py-2 focus:text-sm",
				children: "Skip to content"
			}),
			/* @__PURE__ */ jsx(Masthead, { route }),
			/* @__PURE__ */ jsx("div", {
				id: "main",
				ref: containerRef,
				tabIndex: -1,
				className: "flex-1 outline-none",
				children
			}),
			/* @__PURE__ */ jsx(Footer, {})
		]
	});
}
//#endregion
//#region src/entry-server.tsx
/** Build-time renderer. Runs in Node, renders the SAME components the browser renders.
*
* Two renderers would drift; D-10 says the human surface reads the artefacts the machines read,
* and a second templating path would quietly become a second source of truth. So this imports
* `Shell` and `Body` from the app rather than reproducing them. */
function renderRoute(route, reg, passport) {
	return render(/* @__PURE__ */ jsx(Shell, {
		route,
		children: /* @__PURE__ */ jsx(Body, {
			route,
			reg: reg ? {
				state: "ready",
				data: reg
			} : { state: "loading" },
			passport: route.startsWith("/p/") ? passport ? {
				state: "ready",
				data: passport
			} : { state: "missing" } : null
		})
	}));
}
/** A method note, in the site's own chrome and nothing else.
*
* The note's body is HTML built by `web/notes/emit.mjs` from committed prose - it is a document,
* not a component, and it carries no state for a browser to take over. What it must NOT do is
* reproduce the masthead and the footer: a second copy of the chrome is a second thing to drift,
* and the whole reason `renderRoute` exists is that there is one component set. So the note is
* poured into the same `Shell`, and inherits every token and every rule by construction. */
function renderStatic(route, html) {
	return render(/* @__PURE__ */ jsx(Shell, {
		route,
		children: /* @__PURE__ */ jsx("main", {
			className: "mx-auto max-w-[1180px] px-5 py-8",
			children: /* @__PURE__ */ jsx("div", { dangerouslySetInnerHTML: { __html: html } })
		})
	}));
}
//#endregion
export { PRERENDER_ROUTE, TITLES, renderRoute, renderStatic };
