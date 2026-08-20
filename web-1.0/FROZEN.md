# web-1.0 - structural clone, frozen

This is the phase-2 rollback point of the design method: structure, real data,
neutral palette, no visual decisions taken yet.

It exists so that phases 3-5 (palette, type, states, motion) can be compared
against something rather than against a memory, and so that a wrong direction
costs a copy rather than a rebuild.

Frozen at commit 82d8a29. Do not edit; edit `web/` instead.

Measured before freezing: five routes at 360 / 768 / 1280 / 1920, comparing
document scrollWidth against clientWidth. 20 of 20 with no horizontal overflow.
