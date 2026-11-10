# WStore architecture and migration contract

Status: target architecture, not a claim of implementation or production readiness.
Code inspection date: 2026-11-09. Baseline commit:
`37d089218bb7e584b4b0b076d400ec3f9b25a5b6`.

This document describes the inspected Django application and the architecture to
which it should migrate. The decision is recorded in
[ADR 0001](adr/0001-modular-monolith.md). Concurrent implementation work must be
checked against these requirements; the existence of this document proves none
of the release gates below. No live infrastructure was inspected for this design.

## 1. Existing system and evidence

Paths below are relative to the Django project root.

| Inspected source | Actual responsibility and consequence |
| --- | --- |
| `config/settings.py`, `config/urls.py` | Three installed business apps, `core`, `store`, `orders`; Django templates, sessions, CSRF and UZ/RU/EN localization. `apps/` is added to `sys.path`. `DATABASE_URL` selects a database, otherwise SQLite is used. Existing canonical routes and compatibility aliases are externally visible contracts. |
| `apps/core/models.py` | `User` combines authentication, seller profile, referral attribution and mutable balance. `ApiToken` stores hashed bearer credentials; `ErrorLog` stores diagnostic records. `AUTH_USER_MODEL` is `core.User`. |
| `apps/core/oauth.py`, `views.py`, `profile_views.py` | Google exchange/account linking, password login, demo login, onboarding and token issuance are HTTP-driven. Profile views also query orders and catalog directly. Preserve working entry points while extracting policy. |
| `apps/core/api.py` | Seller authentication, JSON validation, product serialization, slug selection, ORM mutation and sales reports share one module. `product_detail_view` wraps even GET in a transaction with a row lock. |
| `apps/store/models.py`, `views.py`, `forms.py`, `admin.py` | Catalog, uploads, screenshots, reviews, wishlists, reports and moderation. `Product.price` is USD; `price_som` converts using a settings rate and truncates to an integer. `Review.is_verified_buyer` can import `orders.models`. HTML deletion can physically delete an unsold product; API deletion archives it. Admin actions update statuses directly. |
| `apps/orders/views.py` | Checkout, listing payment, provider callbacks, settlement, downloads, dashboards and withdrawals coexist. `order_status_view` can create a payment attempt during GET. Demo and real settlement have separate implementations. |
| `apps/orders/models.py`, `utils.py` | `Order` has UZS amount and a title snapshot, but no immutable seller/rate/commission/archive-version snapshot. `ClickTransaction` references order/product but provider and merchant IDs are not unique. Commission and payment URL construction convert money through `float`. |
| `apps/orders/views.py::click_complete_webhook` | Conditional updates protect a transaction and an order against repeated credits; referral credit also has a conditional guard. However, the PAID replay branch precedes prepare-ID validation, provider identity is not uniquely bound, and a second successful transaction for a paid order is acknowledged without a reconciliation record. These are gaps despite existing replay tests. |
| `apps/orders/admin.py` | Withdrawal rejection conditionally restores balance inside a transaction. Order and Click admin registrations do not declare protected financial fields read-only. All command entry points must eventually share the same policy. |
| `apps/core/telegram.py`, `logging_utils.py` | Telegram HTTP calls run synchronously with a five-second timeout. Settlement uses `on_commit`; other calls run directly after writes. There is no durable notification outbox in the inspected models. `ErrorLog` depends on the database it may be diagnosing. |
| `apps/core/test_api.py`, `test_auth.py`, `apps/orders/test_regressions.py`, `.github/workflows/tests.yml` | Regression coverage exists for ownership, validation, auth, sequential payment retries, downloads and withdrawals. CI runs Django checks, migration drift checks and tests with SQLite. This is not evidence of concurrent PostgreSQL settlement or visual equivalence. |

The existing atomic guards, token hashing, private download authorization and
regression tests are assets to retain. Extracting functions into files alone does
not resolve the ownership, durability and accounting gaps above.

## 2. Decision and boundaries

Use one Django deployment artifact, one transactional PostgreSQL database for the
target production system, and five explicitly owned modules. A separate supervised
notification worker runs the same artifact. SQLite may remain available for fast
local tests, but is not the concurrency certification environment. Introducing
PostgreSQL is a separate rehearsed release, not an incidental settings change.

Logical boundaries do not require renaming existing Django app labels or tables.
Initially, `core` implements identity, `store` implements catalog, and `orders`
contains order and payment persistence behind separate application interfaces.
New payments and notifications packages can be introduced without moving old rows.

| Module | Owns | Public commands / queries | Must not own |
| --- | --- | --- | --- |
| Identity | Users, Google account associations, sessions/authentication policy, seller eligibility, token lifecycle, referral attribution | Authenticate principal; link verified Google account; onboard seller; issue/revoke token; get eligibility and referral attribution | Product writes, checkout, settlement, balance arithmetic |
| Catalog | Categories, product content, publication state, moderation, immutable archive versions, screenshots, reviews, wishlists, reports | Create/update/archive product; moderate; record listing-fee satisfaction; produce purchase quote; get versioned artifact; list/search products | Provider protocol, order status, seller credit |
| Orders | Purchase intent, immutable commercial snapshot, purchase entitlement, download authorization and purchase history | Start/reuse order; accept settlement; cancel/record refund; query paid ownership; authorize download | Click signature parsing, provider HTTP, account ledger, Telegram |
| Payments | Payment intents/attempts, provider identity and receipts, settlement journal, seller accounts, commissions, referral awards, withdrawal reservations and reconciliation | Prepare/record provider result; post financial settlement; reserve/release withdrawal; confirm payout; query account and reconciliation | Template rendering, product moderation decisions, Google identity linking |
| Notifications | Versioned event outbox, delivery jobs, channel rendering, retries and delivery audit | Enqueue event transactionally; claim delivery; deliver/retry/dead-letter | Changing payment, order, catalog or identity state |

Referral attribution stays in identity; the rule awarding a monetary bonus and
its unique financial posting belong to payments. Historical `User.balance`,
`referral_bonus_paid` and card fields are transitional storage, not permission for
identity or profile views to mutate financial state. Payments becomes their sole
writer before moving them to dedicated tables. Public identity profile data and
restricted payout destination data must have separate read permissions.

Orders retain buyer/seller identifiers, product title, USD price, conversion rate,
charged UZS amount, commission policy/version and artifact version at purchase.
Paid ownership survives product archival, price changes and seller profile edits.
Account deletion must not cascade away financial evidence; use deactivation and
an explicit anonymization/retention workflow. Existing CASCADE relations require a
reviewed migration before that invariant can be claimed.

## 3. Dependency direction and composition

The allowed direction inside each module is:

`HTTP/admin/CLI adapter -> application use case -> domain policy + port contracts`.

Infrastructure adapters implement ports and depend inward on their contracts.
Pure monetary rules and state transitions do not import Django requests,
responses, models, settings, `requests`, or provider SDKs. Django ORM models remain
the persistence implementation; do not create a second entity model for every
simple catalog field or a generic repository wrapping every ORM operation.

Cross-module workflows live in a small project application layer, proposed as
`application/workflows/`. It is above all five modules and implements checkout,
purchase settlement and listing-fee settlement. It calls their public interfaces,
owns the shared transaction, and does not import their ORM internals. Module code
never imports this coordinator. `config/composition.py` is the proposed wiring
point that binds interfaces to Django repositories, provider adapters and the
outbox. These are target paths, not files created by this documentation task.

| Dependency | Rule |
| --- | --- |
| Presentation -> workflow or module application API | Allowed; map validated request data and authenticated actor to commands, then map typed results/errors to existing responses. |
| Workflow -> module public command/query contracts | Allowed; explicit coordination and transaction scope, without direct table mutation. |
| Module application -> its domain and ports | Allowed. Ports use IDs, immutable DTOs and typed results, not another module's models or querysets. |
| Module adapter -> its own ORM and external clients | Allowed; legacy cross-app storage access is restricted to named migration adapters. |
| Catalog -> orders, or orders -> payments implementations | Forbidden. Inject a purchase-eligibility query or coordinate outside the modules. |
| Notifications -> business module commands | Forbidden. Delivery cannot settle an order or grant a download. |

For example, verified-buyer badges use an injected purchase-query port implemented
by an orders query adapter, with a batched lookup. Catalog does not import the
orders model. Profile/seller dashboards compose read DTOs at the presentation
application boundary. There is no circular identity/catalog/orders import chain.
Cross-module foreign keys in the shared database are allowed for integrity; they
do not authorize arbitrary cross-module writes or lazy relation access in DTOs.

Use separate command services and query selectors. Named use cases have small,
typed inputs/results and explicit expected errors such as `NotEligible`,
`InvalidTransition`, `Conflict` and `ArtifactUnavailable`. HTTP-specific error
codes and translated flash messages stay in adapters. Authentication establishes
the actor; use cases still enforce ownership and authorization for every entry
point, including admin and management commands.

SOLID is applied through cohesive use cases, narrow consumer-owned protocols and
replaceable provider/storage implementations. Prefer functions where stateful
objects add no value. A new class hierarchy, service locator, microservice or event
bus is not required for every operation.

## 4. Ports and adapters

| Port / contract | Consumer | Concrete responsibility |
| --- | --- | --- |
| `IdentityProvider` | Identity account-linking use case | Google HTTP adapter exchanges a code and validates trusted identity data; use case decides account linking and role policy. Network calls precede the short account write transaction. |
| `ActorEligibility`, `ReferralAttribution` | Purchase workflow | Identity query adapter supplies active account, seller eligibility and referral facts. Never accept seller/buyer IDs as trusted merely because a client supplied them. |
| `CatalogQuote`, `ArtifactStorage` | Checkout/download application services | Quote includes product revision, seller and immutable artifact ID; private Django storage adapter stages/opens files, validates type/size and exposes no public archive URL. |
| `PurchaseEligibility` | Catalog review/read composition | Orders query adapter answers paid ownership in batches without exposing an ORM model. |
| `PaymentGateway` | Payment application service | Click adapter maps raw signed payloads to validated provider DTOs and typed results back to provider response fields. A demo adapter implements the same settlement contract, enabled only in test/development. |
| `UnitOfWork` | Cross-module workflow | Django implementation wraps one database transaction. Nested module calls join it; no module independently commits part of settlement. |
| `EventOutbox` | Business application services/workflows | Django outbox adapter inserts a versioned event in that same transaction. Events contain stable IDs and minimal necessary snapshots. |
| `NotificationChannel` | Delivery worker | Telegram adapter escapes interpolated HTML, applies timeouts and reports retryable/permanent failures. It never receives raw tokens, full card numbers or provider credentials. |
| `Clock`, secure token generator | Time/idempotency-sensitive services | Injectable only where expiry and deterministic tests require them; production adapter uses timezone-aware time and cryptographic randomness. |

An upload is not a database transaction: stage and validate content first, then
attach a durable immutable storage key in a short transaction. Rollback leaves an
unreferenced staged object for safe cleanup. Deletion of referenced artifacts is
forbidden; garbage collection checks references and retention. Download grants
refer to the purchased version, not today's mutable `Product.file_archive`.

## 5. Transaction, money and idempotency contract

### Checkout and quoting

The workflow checks actor, self-purchase, active/nondeleted product, usable payment
configuration and a deliverable archive. Revalidate product revision and eligibility
inside the write transaction after storage checks. Serialize competing checkout
creation for the same buyer/product and enforce uniqueness in the database.
An existing paid entitlement returns its order; a matching active pending intent
is reused. Changed quotes require an explicit new intent, not silent repricing.
GET order/status/poll endpoints do not create orders or payment attempts.

Every money value is a finite `Decimal` plus an explicit currency. Quantize at the
documented boundary and snapshot the rounding policy. Preserve existing whole-UZS
checkout semantics during extraction; adopting fractional UZS or changing
commission rounding is a separately tested business change. Never recalculate an
old transaction from current product price, exchange rate or commission settings.
Provider formatting must agree exactly with the stored charged amount, without
an intermediate `float` conversion.

### Callback processing and settlement

1. The Click adapter bounds/parses the raw body, validates signature or the
   explicitly configured bridge mode, and validates service/action identifiers.
   An invalid direct signature cannot fall back to a bridge secret. Keep raw
   amount representation for signature verification and parsed Decimal for money.
2. The payments service binds provider transaction ID, merchant reference,
   prepare ID, kind, currency and amount to one stored attempt. Perform these
   checks even for a replay of an already paid transaction. A valid signature
   alone does not establish that it belongs to this attempt.
3. The workflow enters one transaction and reloads/locks affected state. It
   claims the provider receipt, records the payment result, transitions the order
   once, creates entitlement and financial postings, records any referral award,
   and inserts outbox events. Listing-fee settlement instead records the paid fee
   and asks catalog to transition an eligible DRAFT to PENDING moderation.
   Payment never directly publishes a product as ACTIVE.
4. Commit before returning success. On rollback none of the entitlement, ledger
   credit or notification event exists. Transient database failure returns a
   retryable provider result; it must not be acknowledged as settled.
5. A committed retry returns the stored protocol result without repeating its
   effects. A different provider transaction paying the same entitlement is a
   reconciliation case: record the real incoming payment, block duplicate seller
   credit, and expose a refund/review task. Do not silently discard a real charge.

Prepare binds an attempt but grants nothing. FAILED/REFUNDED attempts cannot be
resurrected by a delayed completion. Failure of one attempt need not cancel a
still-payable order; order cancellation is its own command. Late payments against
cancelled orders and deleted/changed targets require explicit reconciliation.
Refunds produce compensating financial postings and revoke the affected grant;
they never erase original settlement evidence. Refund support must not be claimed
merely because `REFUNDED` exists in a choices enum.

### Database enforcement

Target constraints, introduced after checking and resolving existing duplicates:

| Invariant | Required enforcement |
| --- | --- |
| Client command replay | Unique `(actor, operation, idempotency_key)` plus request fingerprint and stored result; same key/different body is a conflict. Scope keys by tenant/actor. |
| One active checkout / entitlement | Unique active pending intent per buyer/product, plus one applicable paid entitlement per buyer/product under the current single-purchase policy. Partial uniqueness and guarded transitions must cover concurrent submissions. |
| Provider binding | Unique merchant reference and unique nonempty `(provider, provider_transaction_id)` on the attempt; separate prepare/complete receipt uniqueness by attempt and action. Preserve existing `WSTP`/`WSTL` references. |
| Seller credit | Unique settlement posting per order/effect, irrespective of how many attempts completed. |
| Referral reward | Unique award per referred buyer under the current first-purchase policy; record beneficiary and amount, not only a boolean. |
| Withdrawal reservation/release | Unique posting per withdrawal/effect; guarded state transition and sufficient available funds in the same transaction. |
| Durable event/delivery | Unique event ID and `(event_id, channel, recipient)` delivery key. |

Ledger transactions are immutable and balanced per currency: receipt, platform
commission, seller payable, referral expense and payout movements have explicit
accounts. Refunds and rejection releases reference their original postings.
Available seller balance is a validated projection; withdrawal reserves funds
atomically and requires amount > 0 and available balance >= amount. A payout
confirmation requires an external payment reference and actor audit. Retrying
approval or rejection cannot send money or release a reservation twice.

Use a documented global lock order where resources overlap: product, order,
payment attempt, withdrawal, then account rows sorted by stable ID. Discover IDs
before locking and revalidate them under lock. A path may skip irrelevant resources
but may not acquire an earlier class after a later one. Use conditional updates
and database constraints as the final protection; deadlock/serialization retries
repeat the whole idempotent transaction with a bounded retry policy. No network
or file upload occurs while locks are held. Test these semantics with independent
connections on PostgreSQL; SQLite tests cannot certify row locks.

### Durable notifications

`transaction.on_commit` may wake a worker but is not the delivery record. Insert
the event and delivery intent in the business transaction. A worker claims a
bounded batch using leases, commits the claim, sends outside the transaction,
then records the result. Expired leases are recoverable after worker death.
Use capped exponential backoff, attempt limits, dead-letter inspection and explicit
operator replay. Monitor oldest pending age and failures.

Delivery is at least once. A crash after Telegram accepts a message but before
recording success can produce a duplicate; do not promise exactly-once external
delivery. This cannot duplicate financial effects, and it cannot roll back a
successful customer payment. Channel failures remain visible operationally.

## 6. Incremental migration from current apps

Every row is a reviewable stage with a rollback boundary. Keep a single active
writer for each operation; do not dual-write old and new settlement paths.

| Stage | Current code -> target seam | Acceptance and rollback |
| --- | --- | --- |
| 0: characterize | `config/urls.py`, templates, static assets and existing tests -> recorded HTTP/UI contracts | Inventory route aliases, JSON fields, redirect targets, form errors, UZ/RU/EN, dark/light and mobile/desktop states. Record real production database/config separately. No behavioral cutover. |
| 1: identity | `core/oauth.py`, `views.py`, token/profile mutations -> identity services with Google/token adapters | Preserve state checking, verified-email linking, disabled-user rejection, existing sessions and password/Google entry points. Keep `core.User`, its PKs and migration label. Roll back code without changing auth tables. |
| 2: catalog | `core/api.py` product commands, `store/views.py`, forms and admin actions -> one catalog command API and selectors | Same owner/eligibility/moderation rules across API, HTML and admin. Archive consistently; protect referenced content. Centralize validation/slug collision handling. Characterization and race tests pass before redirecting each caller. |
| 3: orders and queries | Checkout/status/download portions of `orders/views.py`, profile/stats aggregates -> order services and presentation query composition | GET becomes read-only; POST starts/retries checkout. Preserve URL and display behavior. Backfill seller/price/artifact snapshots additively; mark unrecoverable historical facts unknown rather than inventing them. Old releases tolerate nullable fields. |
| 4: payment extraction | `orders/utils.py`, prepare/complete handlers, demo branches and withdrawal/admin mutations -> Click adapter, payment services and workflow coordinator | First preserve verified provider contracts and existing IDs; then add durable receipts, uniqueness, journal, shared settlement and outbox. Route all entry points through one writer. Replays/concurrent attempts cannot duplicate economic effects. |
| 5: financial migration | `core.User.balance`, referral flag and existing withdrawals -> payments-owned accounts, opening postings and reservations | Reconcile legacy balances at a recorded cutoff. Import opening balances, not invented historic transactions. Preserve pending reserved amounts and avoid deducting them again. Compare per-user totals, outstanding withdrawals, paid orders and provider IDs before switching reads. |
| 6: notification migration | `core.telegram.send_telegram_notification`, callback `on_commit` sends -> durable outbox and channel worker | Switch producer paths once; no simultaneous direct send plus queued send. Test failure before commit, after commit, after send and worker restart. Worker lag/errors have an operator-visible alert. |
| 7: production cutover | SQLite fallback/deployment procedure -> validated PostgreSQL release and operational controls | Rehearse import, restore and concurrent settlement. Enable the new release only after migration, data reconciliation, private media, readiness and UI checks pass. Keep old schema until rollback compatibility expires. |

Payment and notification stages are released together where settlement durability
requires both; extracting a provider adapter can precede schema changes. The
PostgreSQL rehearsal can run in parallel, but database constraints and concurrency
gates must pass before enabling new financial writes in production.

Do not rename installed app labels or rewrite applied migrations during service
extraction. `core/migrations/0003_*` already depends on `store.0001_initial` and
uses historical models for seller backfill. Moving a physical model later needs
a separate migration design covering table identity, content types, permissions,
foreign keys and migration state. Existing `AUTH_USER_MODEL` remains `core.User`.

## 7. UI and API compatibility

Preserve Django server rendering, template names/context contracts, CSS/JS hooks,
forms, gallery layout, themes, localization and responsive design. Keep all route
names and compatibility aliases in `config/urls.py`, `core/urls.py`,
`core/api_urls.py`, `store/urls.py` and `orders/urls.py`, including callback variants
with and without trailing slash. A provider redirect is not proof of payment.

Presentation adapters may build compatibility view models so templates no longer
trigger database/storage access accidentally. API v1 retains its documented JSON
shape while internals use exact money values; switching public numeric money to
strings needs an explicit version/compatibility decision. New errors and stronger
authorization must be deliberate, tested contract changes, not accidental effects
of moving code. The refactor does not introduce a SPA, change the visual design or
remove existing authentication methods.

## 8. Security, operations and release gates

- Fail startup for unsafe production configuration: debug/demo enabled, missing
  application secret, invalid origins or incomplete selected payment adapter.
  Provider-not-configured checkout stays unavailable with an existing-style user
  message. Secrets are injected, rotated and excluded from logs and repositories.
- Enforce ownership, actor capability and state in services. Restrict bearer tokens
  to the seller's operations, preserve one-time raw token display and revocation,
  and rate-limit authentication, token endpoints and expensive reads. Browser
  mutations retain CSRF. Only authenticated provider callbacks bypass browser CSRF.
- Keep archives outside public media serving. Bound request/upload sizes, verify
  content and safe filenames, escape Telegram/HTML content and validate remote URL
  schemes. Do not fetch arbitrary seller URLs from the server without an explicit
  outbound-network policy.
- Emit structured, redacted logs with request/command ID, order ID, attempt ID,
  outcome and duration. Maintain financial/moderation audit records with actor and
  reason. Operational logging must work during database failure; `ErrorLog` is an
  optional support view, not the only sink.
- Expose distinct liveness and readiness checks; monitor HTTP errors/latency, DB
  contention, rejected callbacks, reconciliation backlog, outbox age, worker
  heartbeat, missing artifacts and disk capacity. Check provider outages separately
  so a Telegram failure cannot make a healthy storefront unready.
- CI must enforce agreed PEP 8-compatible lint/format rules, typed service/port
  boundaries, dependency direction, migration drift and repeatable dependency
  installation. Run pure policy tests, adapter contract tests, Django regressions,
  PostgreSQL transaction/concurrency tests, and browser checks of preserved flows.
  Pin the supported Python/Django/dependency set; review upgrades explicitly.
- Financial acceptance scenarios include two simultaneous checkouts, duplicate and
  conflicting callbacks, completion after cancellation, two real payments for one
  order, concurrent withdrawals, refund/rejection replay and crash recovery. Verify
  both final balances and the journal/outbox rows, not only HTTP 200 responses.
- Rehearse restore of database and private media together. Record actual backup
  locations, release hash, runtime versions and recovery timings for each release;
  choose outage/recovery targets using measured production capacity, not assumed
  server specifications from previous conversations.

For SQLite-to-PostgreSQL migration, use a staging copy first; validate counts, PKs,
FKs, amounts, time zones, token hashes and sequences. At cutover freeze application
writes and pause workers, then take a consistent final snapshot. Provider callbacks
must receive retryable failure during that interval, not success without a durable
write; rehearse provider retry/reconciliation before scheduling the freeze. Restore,
validate, switch configuration, check readiness and only then reopen writes.

Before reopening writes, rollback may restore the original configuration and
database. After accepting new writes on PostgreSQL, switching to an old SQLite
snapshot would lose transactions: use a compatible application rollback on the
new database or a reconciled recovery procedure. Additive schema changes keep the
previous release runnable; destructive contraction is a later release.

The existing deployment instructions identify `/opt/wstore`, `wstore.service` and
nginx's `staticfiles/` directory. Revalidate those paths on the target host. Build
static assets/translations before switching the app, run deployment/migration
checks, and verify the new asset version after restart. Keep credentials, media
and database state outside code synchronization. A complete release requires
current runtime and visual evidence; passing unit tests alone is insufficient.
