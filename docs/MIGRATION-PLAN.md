# Migration plan: adding the copilot with zero host schema breakage

The goal is to add the copilot to a running production database without altering, locking, or
risking any existing table, and to be able to remove it just as cleanly.

## What the copilot adds

Four new tables, all additive, all prefixed `copilot_`:

| Table | Purpose |
| --- | --- |
| `copilot_tenant_config` | Per-tenant enable flag and optional token budget override |
| `copilot_embedding` | Semantic-search vectors, referencing host rows by `(source_table, source_pk)` |
| `copilot_response_cache` | Cached model responses keyed by redacted prompt hash |
| `copilot_usage_log` | Per-call token accounting for budgets and cost reporting |

No `ForeignKey` points at a host table; references are plain integer ids. The migration
(`copilot/migrations/0001_initial.py`) has an **empty `dependencies` list**, so it can be
applied independently of the host's migration history.

## Why it is backward compatible

- **No `ALTER TABLE` on host tables.** Only `CREATE TABLE`s run, so existing rows are untouched
  and the change does not take table locks on hot tables.
- **No FK to host tables.** Adding an FK would require an index/constraint against a possibly
  large host table and couple the migration graphs. Integer references avoid both.
- **Reads use the ORM against existing tables** (summarize) or **read-only tenant-scoped views**
  (ask-your-data). Nothing the copilot does mutates host data.
- **Enforced by tests.** `tests/test_migration_safety.py` fails the build if a future migration
  ever touches a `helpdesk_` table or adds a dependency on the host app.

## Rollout steps

1. Deploy the code with `COPILOT_ENABLED=false` (global kill-switch off). No behavior changes.
2. Run `python manage.py migrate copilot`. Only the four additive tables are created.
3. Build the search index: `python manage.py copilot_seed_embeddings` (idempotent
   `update_or_create`; safe to re-run).
4. Enable for one pilot tenant by creating a `CopilotTenantConfig(tenant_id=…, enabled=True)`
   with a conservative `daily_token_budget`.
5. Flip `COPILOT_ENABLED=true`. Only tenants explicitly enabled see the feature.
6. Widen the pilot tenant by tenant, watching `copilot_cost_report`.

## Rollback

- **Instant, no migration:** set `COPILOT_ENABLED=false`, or set the tenant's
  `CopilotTenantConfig.enabled=false`. The feature disappears; host app is unaffected.
- **Full removal:** `python manage.py migrate copilot zero` drops only the four `copilot_`
  tables. Because nothing in the host schema references them, this is safe and leaves the host
  database byte-for-byte as it was before step 2.

## Re-indexing

`copilot_seed_embeddings` re-embeds all tickets and upserts by `(source_table, source_pk)`, so
it is safe to run on a schedule or after a backfill. Switching the embedding backend (e.g.
hashing → Voyage) changes vector dimensionality, so re-index the whole corpus when you change
`COPILOT_EMBEDDING_BACKEND`.
