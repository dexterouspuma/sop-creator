# Engineering Standards — SOP / Training Document Creator

> **Status:** v1 (living document). This is the authoritative engineering context for any
> agent or developer working on this codebase.
>
> **How to use this file:** Read it before writing or changing code. The rules in
> **§2 Non-Negotiable Invariants** must never be violated. If a task seems to require
> breaking one, STOP and ask a human — do not work around it. Everything else is a
> strong default; deviate only with a stated reason.

---

## 1. Product Context

We are building a **SOP / Training Document Creator**: a cloud application for authoring
Standard Operating Procedures and training material, managing their full controlled
lifecycle, and tracking that the right people have read and acknowledged the right version.

Core lifecycle every document moves through:
`draft → review → approve → publish → assign as training → acknowledge → revise → archive`

Key facts that shape the architecture:
- **Tenancy:** Multi-tenant SaaS. We may launch with a single customer, but the system is
  multi-tenant from day one. Some tenants may later need full data isolation.
- **Regulation:** Mixed. Some tenants operate in regulated industries (pharma, medical
  devices, food, aviation) subject to standards like FDA 21 CFR Part 11, EU Annex 11, and
  ISO 9001 document control. Compliance *primitives* are built for everyone; compliance
  *features* are configurable per tenant.
- **AI:** AI-assisted drafting is a core feature, not an add-on.

---

## 2. Non-Negotiable Invariants

These are hard rules. Never break them without explicit human approval.

1. **Tenant isolation.** Every tenant-owned table has a `tenant_id`. Every query that
   reads or writes tenant data filters by `tenant_id`. No query may return or modify data
   across tenant boundaries. Prefer database-enforced isolation (e.g. Postgres Row-Level
   Security) over relying on application code alone.

2. **Append-only audit log.** Every state-changing action on a document (create, edit,
   submit, review, approve, publish, assign, acknowledge, archive) writes an immutable
   audit record: who, what, when, the affected entity + version, and where applicable why.
   Audit records are never updated or deleted. This table is treated as tamper-evident.

3. **Version immutability.** Once a document version exists, its content is never mutated.
   Changes create a new version; old versions are superseded, never overwritten. The system
   can always show what a given version said and what changed between any two versions.

4. **AI never self-approves.** AI-generated or AI-assisted content enters the *same*
   controlled lifecycle as human content. It is always a draft requiring human review, and
   no AI output may reach an "approved" state without an accountable human actor recorded in
   the audit log. The audit trail records that a document was AI-assisted.

5. **Identity is always known.** Every action is attributable to an authenticated user.
   No anonymous or service-only paths may create, approve, or acknowledge documents on a
   user's behalf without that being explicit and logged.

6. **Secrets never in code.** No credentials, API keys, tokens, or connection strings in
   source, config files committed to the repo, or logs. Use environment variables / a
   secrets manager.

7. **Encryption.** All data encrypted in transit (TLS) and at rest.

---

## 3. Architecture Standards

- **Shape:** Modular monolith. Organize by domain module (e.g. `documents`, `versions`,
  `workflow`, `training`, `tenancy`, `audit`, `ai`) with clear internal boundaries. Do NOT
  split into microservices without an explicit decision — we are not at that scale.
- **Statelessness:** Application processes are stateless; no session state on local disk or
  in process memory. (Twelve-Factor App principles apply throughout.)
- **Config:** All environment-specific config comes from the environment, not from code.
- **Primary datastore:** PostgreSQL. Use relational tables for the lifecycle/workflow and
  JSONB for flexible document body content. Use Row-Level Security for tenant isolation.
- **File storage:** Object storage (e.g. S3-compatible) for exported PDFs/DOCX and binary
  attachments. Never store large binaries in the database.
- **AI access:** All LLM calls go through a single internal service/abstraction layer.
  No part of the app calls a model provider SDK directly. Providers and models must be
  swappable via config without touching feature code.
- **Logs:** Treat logs as event streams to stdout; do not write app logs to local files.

---

## 4. Security & Compliance Baseline

- Follow the **OWASP Top 10**; validate and sanitize all input; use parameterized queries.
- **AuthN/AuthZ:** Centralized authentication. Role-based access with least privilege.
  Author, reviewer, approver, and admin are distinct roles; enforce separation of duties in
  approval workflows (the same user cannot author and solely approve where a tenant requires
  segregation).
- **Audit fields:** Standard audit columns (`created_at`, `created_by`, `tenant_id`) on all
  records, plus the dedicated append-only audit log from §2.
- **E-signature readiness:** Approval actions are structured so a compliant electronic
  signature (identity + intent + timestamp, bound to the specific version) can be enforced
  per tenant. Build the data model to support this even where it is not yet enforced.
- **Data residency / isolation hooks:** Design so a sensitive tenant can later be moved to
  an isolated database or region without a rewrite.

---

## 5. AI Integration Standards

- **Human-in-the-loop is mandatory** (see Invariant 4).
- **Ground, don't invent.** Prefer generation grounded in the tenant's own reference
  material (retrieval over free invention) to reduce hallucination. A subtly wrong SOP is
  worse than no SOP.
- **Provider data terms:** Use providers/configurations with appropriate enterprise data
  handling; confirm retention terms (e.g. zero-data-retention options) per provider before
  sending tenant content. Allow sensitive tenants to restrict or disable AI features.
- **Metering:** Record per-tenant AI usage (tokens/requests). This serves both billing and
  abuse protection.
- **Traceability:** Log which model/version produced an AI draft and associate it with the
  resulting document version.
- **Resilience:** Handle provider timeouts/errors gracefully; AI failure must never corrupt
  or block the core document workflow.

---

## 6. Coding Standards

> TODO: finalize once language/framework is chosen (see §10). General rules below apply
> regardless of stack.

- Use a statically/strongly typed language or strict typing where available.
- Enforce a formatter and linter in CI; code must pass both before merge.
- Small, focused modules and functions; clear naming over cleverness.
- Explicit, structured error handling — no silently swallowed errors.
- No secrets, no commented-out dead code, no TODOs left unexplained in merged code.

---

## 7. Testing & Quality Gates

- Unit tests for domain logic; integration tests for workflow and persistence.
- **The invariants in §2 must have explicit tests** (tenant isolation leak tests, version
  immutability tests, audit-record-written tests, no-AI-auto-approve test).
- CI runs lint + format + tests on every change; merges are blocked if any fail.

---

## 8. Version Control & Delivery

- Small, reviewable changes; descriptive commit messages.
- No direct commits to the main branch; changes land via reviewed pull requests.
- **Infrastructure as Code** for all environments — no hand-configured "click-ops" infra.
- CI/CD pipeline handles automated testing and deployment.

---

## 9. Definition of Done

A change is done only when:
- [ ] It satisfies every applicable invariant in §2.
- [ ] Tenant filtering is present on all new data access.
- [ ] State changes write an audit record.
- [ ] Tests (including invariant tests) are written and passing.
- [ ] Lint/format/CI are green.
- [ ] No secrets in code; config externalized.
- [ ] Docs/this file updated if a standard or decision changed.

---

## 10. Open Decisions (resolve before relying on §6 specifics)

- [ ] **Language / framework** for backend (and frontend).
- [ ] **Cloud provider** (AWS / GCP / Azure).
- [ ] **AI provider(s)** and model selection.
- [ ] **Authentication approach** (build vs. managed identity provider).
- [ ] **Initial compliance target tier** (which regulated standard to support first).

> When a decision here is made, record it (a short Architecture Decision Record is ideal)
> and update the relevant section above.

---

## 11. Hard "Do Not" List

- Do NOT query tenant data without a `tenant_id` filter.
- Do NOT mutate or delete an existing document version or audit record.
- Do NOT allow AI output to reach "approved" without a recorded human approver.
- Do NOT put secrets in source or logs.
- Do NOT introduce microservices, new datastores, or new external services without an
  explicit decision recorded in §10.
- Do NOT disable, weaken, or bypass an invariant to make a task easier — ask a human first.
