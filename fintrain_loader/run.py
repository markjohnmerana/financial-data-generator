
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))



import argparse
import json
import time
from typing import Iterable, Sequence

from fintrain_loader.core import Database, LoadState, LoaderConfig, jsonable_row, max_batch_for_columns
from fintrain_loader.tables import build_modules


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load messy financial training data into PostgreSQL.")
    parser.add_argument("--env-file", default=".env", help="Path to the .env file.")
    parser.add_argument("--db-host")
    parser.add_argument("--db-port")
    parser.add_argument("--db-name")
    parser.add_argument("--db-user")
    parser.add_argument("--db-password")
    parser.add_argument("--db-schema")
    parser.add_argument("--scale", choices=("tiny", "small", "medium", "large", "xlarge"))
    parser.add_argument("--payment-orders", type=int, help="Override the payment order count while keeping the same scale shape.")
    parser.add_argument("--batch-size", type=int, help="Maximum rows per insert statement.")
    parser.add_argument("--preview-rows", type=int, help="How many preview rows to show for --dry-run.")
    parser.add_argument("--seed", type=int, help="Deterministic seed.")
    parser.add_argument("--only", help="Run a single table module by name.")
    parser.add_argument("--dry-run", action="store_true", help="Generate sample rows without writing to PostgreSQL.")
    parser.add_argument("--truncate", action="store_true", help="Truncate all target tables before loading.")
    parser.add_argument("--list-tables", action="store_true", help="List available table modules and exit.")
    return parser.parse_args()


def chunked(iterator: Iterable[Sequence[object]], chunk_size: int) -> Iterable[list[Sequence[object]]]:
    batch: list[Sequence[object]] = []
    for row in iterator:
        batch.append(row)
        if len(batch) >= chunk_size:
            yield batch
            batch = []
    if batch:
        yield batch


def preview_module(module, state: LoadState, preview_rows: int) -> None:
    samples = []
    for row in module.iter_rows(state):
        samples.append(jsonable_row(module.columns, row))
        if len(samples) >= preview_rows:
            break
    print(f"\n[{module.name}] preview")
    print(json.dumps(samples, indent=2))


def load_module(module, state: LoadState, db: Database) -> int:
    batch_size = max_batch_for_columns(state.config.batch_size, len(module.columns))
    total_rows = 0
    started_at = time.perf_counter()
    for batch_index, batch in enumerate(chunked(module.iter_rows(state), batch_size), start=1):
        written = db.insert_rows(module.name, module.columns, batch)
        total_rows += written
        if batch_index == 1 or batch_index % 25 == 0:
            print(f"[{module.name}] inserted {total_rows:,} rows")
    elapsed = time.perf_counter() - started_at
    print(f"[{module.name}] complete: {total_rows:,} rows in {elapsed:.1f}s")
    return total_rows


def main() -> int:
    args = parse_args()
    modules = build_modules()
    if args.list_tables:
        for module in modules:
            print(module.name)
        return 0

    config = LoaderConfig.from_args(args)
    state = LoadState(config)
    selected = [module for module in modules if config.only_table in (None, module.name)]
    if not selected:
        raise SystemExit(f"Unknown table module '{config.only_table}'. Run with --list-tables to see options.")

    print(
        f"scale={config.scale} customers={config.row_targets.customers:,} "
        f"payment_orders={config.row_targets.payment_orders:,} dry_run={config.dry_run}"
    )

    if config.dry_run:
        for module in selected:
            preview_module(module, state, config.preview_rows)
        return 0

    with Database(config) as db:
        if config.truncate:
            db.truncate_tables([module.name for module in reversed(modules)])
            print("Target tables truncated.")
        for module in selected:
            load_module(module, state, db)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
