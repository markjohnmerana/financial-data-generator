# Financial Transaction Training Ground

This starter pack gives  a realistic PostgreSQL schema for a payments platform with a double-entry ledger, plus a modular Python loader that can push messy training data into PostgreSQL at large scale. The generator is deterministic, so the same row index always recreates the same record, which makes debugging much easier.

## What's in the schema

Sixteen tables split across four layers:

1. Reference and ownership: `currencies`, `legal_entities`, `customers`, `customer_addresses`, `customer_identities`
2. Money movement edges: `counterparties`, `payment_methods`, `fx_rates`, `settlement_batches`
3. Accounting core: `accounts`, `account_balances`, `journal_entries`, `journal_entry_lines`
4. Transaction flow: `payment_orders`, `payment_order_events`, `authorization_holds`

## Files

- `db/01_financial_training_schema.sql` creates the schema, constraints, indexes, and triggers.
- `db/02_seed_data.sql` inserts a small training dataset with two customers, a payout flow, a settlement batch, and matching journal entries.
- `load_fintrain_data.py` is the CLI entrypoint for bulk loading generated data.
- `fintrain_loader/core.py` contains the shared config, deterministic data logic, and PostgreSQL writer.
- `fintrain_loader/tables/` contains one module per table so you can debug generators in isolation.
- `.env` holds database connection settings for the loader.
- `requirements.txt` lists the Python dependency for PostgreSQL access.

## How to load in DBeaver

1. Create a new PostgreSQL database `financial_training`.
2. Open `db/01_financial_training_schema.sql` in DBeaver and run it.
3. Open `db/02_seed_data.sql` in DBeaver and run it.
4. Refresh the database navigator and expand the `fintrain` schema.

## Python loader setup

1. Install the dependency from `requirements.txt`.
2. Update `.env` with your PostgreSQL connection values.
3. Run the loader from this folder.

Example commands:

```bash
python load_fintrain_data.py --dry-run --only customers
python load_fintrain_data.py --truncate --scale small
python load_fintrain_data.py --truncate --scale large --payment-orders 1000000
python load_fintrain_data.py --only payment_orders
```

If your Windows machine uses `py` or a virtual environment path instead of `python`, use that interpreter instead.

## How the loader is organized

- One table = one module. Every table under `fintrain_loader/tables/` has its own generator.
- Shared deterministic logic lives in `fintrain_loader/core.py`.
- `--only <table_name>` lets you debug a single table generator.
- `--dry-run` prints sample rows without inserting anything.
- `--truncate` clears the target tables before reloading.
- Scale presets go from `tiny` to `xlarge`, with `xlarge` sized for multi-million-row training runs.

## What kinds of mess are included

- Sparse optional fields like missing email, phone, postal code, line2, and external references.
- Inconsistent text formatting like extra spaces, mixed casing, retry suffixes, and legacy-style identifiers.
- Mixed operational statuses like pending review, restricted, suspended, failed, reversed, expired, and draft accounting rows.
- Timing mess like old-but-open items, delayed completions, expired holds, and journal lag.
- Transaction shape variation across inbound, outbound, and internal flows.
- Partial accounting coverage on some rows so you can practice gap detection queries.

## Important modeling choices

- All business identifiers use UUIDs so you can practice integration-safe patterns.
- Monetary values are stored as `*_minor` integers, so `50000` means `500.00` in a 2-decimal currency like PHP.
- `payment_orders` is the operational record; `journal_entries` and `journal_entry_lines` are the accounting record.
- `payment_order_events` stores lifecycle history instead of overwriting a single status without an audit trail.
- `account_balances.posted_balance_minor` is signed in a debit-minus-credit direction. That means asset accounts usually trend positive, while liability and revenue accounts usually trend negative.
- `available_balance_minor` is generated from posted balance plus pending inflow minus pending outflow.
- The loader writes in batches and automatically caps batch size so it stays under PostgreSQL parameter limits.
