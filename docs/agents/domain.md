# Domain docs: single-context

- `GLOSSARY.md` at repo root defines all domain terms. `docs/adr/` holds architecture decision records.
- **Consumer rules**: before implementing a ticket, read `GLOSSARY.md` terms it touches and the ADRs listed in it. Terms are canonical — use the exact vocabulary (Router/Tool Selection Layer, Trajectory & Convergence Layer, Outcome Layer, Containment Layer, Attempted Radius, Achieved Radius, Convergence Score, Capability Evals, Regression Evals) in code, UI copy, and docs. If code contradicts a term, fix the code or open an ADR — never invent a synonym.