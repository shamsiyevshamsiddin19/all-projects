# ADR 0001: Evolve WStore into a modular Django monolith

- Date: 2026-11-09
- Status: proposed target; implementation and production migration are not complete
- Scope: identity, catalog, orders, payments and notifications
- Baseline inspected: `37d089218bb7e584b4b0b076d400ec3f9b25a5b6`
- Detailed contract: [Architecture and migration plan](../README.md)

## Context

WStore is an existing Django application with `core`, `store` and `orders` apps,
server-rendered templates, Google/password login, seller bearer-token API, catalog,
Click checkout, private downloads and seller withdrawals. Its visual design and
public URLs must remain intact.

Inspection of `apps/orders/views.py` shows provider parsing, payment transitions,
order fulfillment, mutable user balances and notifications in HTTP handlers.
`apps/core/api.py` repeats catalog policies also implemented in HTML and admin.
`apps/store/models.py::Review.is_verified_buyer` imports orders, while order views
import catalog and identity models. `core.User` stores both identity and money.

There are useful protections: hashed API tokens, conditional settlement updates,
atomic withdrawal deductions and regression tests. However, provider IDs lack
database uniqueness, financial calculations use floats in `orders/utils.py`,
GET order rendering may create attempts, and `on_commit` Telegram delivery cannot
recover a lost message after process death. The existing SQLite CI does not prove
PostgreSQL concurrency behavior. These are architectural responsibilities and
invariants to address explicitly, not just formatting problems.

## Decision

Retain Django and evolve the application into a modular monolith with one
transactional production database and one versioned release artifact. Use
PostgreSQL for production financial concurrency and a supervised worker from the
same artifact for durable notification delivery. Migrate incrementally through
services and adapters while preserving the UI, data identity and external routes.

The five ownership boundaries are:

1. **Identity:** users, account linking, seller eligibility, credentials and referral
   attribution. Keep `AUTH_USER_MODEL = core.User` during extraction.
2. **Catalog:** product content, publication/moderation, versioned private artifacts,
   categories, reviews, wishlists and reports.
3. **Orders:** purchase intent, commercial snapshots, paid entitlement, download
   authorization and purchase history.
4. **Payments:** provider attempts/receipts, exact monetary policy, settlement
   journal, seller accounts, referral awards, withdrawals and reconciliation.
5. **Notifications:** transactional event storage, delivery state, channel rendering
   and retry/dead-letter processing.

These are logical ownership boundaries, not a requirement to rename every Django
app/table immediately. Legacy financial fields on `core.User` become payments-only
storage through an explicit adapter until account migration. Existing order and
Click tables keep their IDs and references through the transition.

HTTP, API, admin and CLI adapters invoke the same application commands. Application
services depend on domain rules and narrow ports; infrastructure implements those
ports. Pure rules do not depend on Django HTTP/ORM or provider clients. A small
project workflow layer coordinates public module interfaces and owns transactions
that span modules. Composition wires adapters outside the modules. No module
imports the coordinator, and no circular catalog/orders/payment service imports
are permitted. Cross-module reads use typed queries or presentation composition.

Use explicit ports for payment provider, Google identity, private storage, durable
outbox and unit of work. Do not impose a generic repository or one class per trivial
operation. Django ORM remains the persistence adapter, and database foreign keys
remain useful integrity mechanisms inside the shared database.

## Non-negotiable consistency rules

- Checkout snapshots charged currency/amount, seller, rate, commission policy and
  artifact version; later product changes cannot alter a paid entitlement.
- Persist and constrain idempotency keys, provider bindings and effect identifiers.
  A signed replay with conflicting identity/amount is not accepted merely because
  an order is already paid. Different real payments for one order enter explicit
  reconciliation rather than creating duplicate seller credit.
- Payment receipt, order transition, entitlement, financial journal and outbox
  insert commit together. Listing payment records fee satisfaction and requests
  moderation; it does not publish a product directly.
- Monetary arithmetic uses finite Decimal values with documented rounding.
  Withdrawals reserve available funds; rejection/refund creates a single
  compensating posting. Financial state cannot be edited through generic admin
  fields or bypassed through a demo-only settlement implementation.
- Network delivery runs outside database transactions. Outbox polling survives
  commit/process failures; `on_commit` is only an optional wakeup. External delivery
  is at least once, with possible duplicate messages after ambiguous send outcomes.
- GET renders/queries state. Financial creation, retries and approvals are explicit
  authorized commands. All writers use the same service invariants.

## Alternatives considered

| Alternative | Assessment |
| --- | --- |
| Extract a few helper functions but keep views/admin as independent writers | Low initial effort, but preserves divergent policy and bypasses transaction/idempotency invariants. Rejected as the final architecture. |
| Rewrite the frontend and backend together | Adds compatibility and delivery risk without solving the requested backend ownership problem. Conflicts with preserving the Django UI. Rejected. |
| Split identity/catalog/orders/payments into network microservices now | Requires distributed consistency, separate deployment/operations and more failure recovery before WStore has established module contracts. No measured need justifies that cost. Deferred. |
| Modular monolith with ports, explicit use cases and shared transactions | Supports incremental releases, clear ownership, testable financial policy and existing Django deployment/UI. Selected. |
| Require a fully separate domain entity/repository for every Django model | Adds mapping and abstraction cost for simple CRUD without a corresponding policy boundary. Rejected as a blanket requirement. |

## Consequences

The design keeps one deployment and makes purchase settlement locally atomic.
Provider, storage and notification behavior become contract-testable. HTML, API
and admin share policy. Database migration risk is separated from code movement.

The monolith still shares failure domains, database capacity and release cadence.
Module boundaries require enforcement through dependency tests, ownership and code
review; directories alone are insufficient. A durable worker, ledger and
reconciliation tooling add operational responsibilities. PostgreSQL deployment and
backup/restore must be rehearsed. Compatibility adapters are temporary and must
have a named removal stage; there must never be two active financial writers.

Retaining old app labels means conceptual and physical ownership differ during
migration. That is deliberate: renaming `core.User` or existing migration history
would endanger authentication, foreign keys, content types and permissions. Later
physical moves require a separate migration decision with recovery evidence.

## Adoption and verification

Follow the staged map in the architecture README: establish HTTP/UI behavior,
extract identity and catalog, isolate order/query workflows, unify payment and
withdrawal commands, introduce constrained financial records and durable outbox,
then complete rehearsed production cutover. Add fields/tables first, backfill and
reconcile, switch a single writer, and remove old paths only after the rollback
window. Preserve legacy merchant references, download URLs and callback aliases.

Before financial cutover, prove concurrency/idempotency on PostgreSQL, durable
delivery under injected crashes, balance/withdrawal reconciliation, artifact access
control and compatibility of the previous app release with additive schema changes.
Backfilled opening balances must not pretend to reconstruct unknown historical
transactions. Once the new database accepts writes, a stale-database rollback is
not an acceptable recovery procedure.

Acceptance also requires enforced lint/format/type/import checks, adapter and
integration tests, structured redacted logs, readiness and worker monitoring,
tested database/media restore, and browser evidence for the existing mobile and
desktop design in both themes and supported languages. Record actual results in
release evidence. This ADR itself neither runs those checks nor authorizes claiming
they passed.

Revisit service extraction only when measured scaling, isolation or independent
release needs justify it. The modular contracts make that future choice possible;
microservice deployment is not the success criterion for this refactor.
