from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import random
import uuid
from dataclasses import dataclass
from decimal import Decimal
from itertools import chain
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence


CURRENCY_ROWS: list[dict[str, Any]] = [
    {"code": "PHP", "numeric_code": "608", "name": "Philippine Peso", "minor_unit": 2, "symbol": "PHP"},
    {"code": "USD", "numeric_code": "840", "name": "US Dollar", "minor_unit": 2, "symbol": "USD"},
    {"code": "EUR", "numeric_code": "978", "name": "Euro", "minor_unit": 2, "symbol": "EUR"},
    {"code": "JPY", "numeric_code": "392", "name": "Japanese Yen", "minor_unit": 0, "symbol": "JPY"},
    {"code": "SGD", "numeric_code": "702", "name": "Singapore Dollar", "minor_unit": 2, "symbol": "SGD"},
    {"code": "GBP", "numeric_code": "826", "name": "Pound Sterling", "minor_unit": 2, "symbol": "GBP"},
    {"code": "AUD", "numeric_code": "036", "name": "Australian Dollar", "minor_unit": 2, "symbol": "AUD"},
]

BASE_ENTITY_CURRENCIES = ("PHP", "USD", "EUR", "SGD")
COUNTRY_BY_CURRENCY = {"PHP": "PH", "USD": "US", "EUR": "DE", "SGD": "SG"}
COUNTRY_POOL = ("PH", "US", "SG", "GB", "JP", "AU", "DE")
EMAIL_DOMAINS = ("example.com", "mail.test", "corp.local", "legacy.net", "sandbox.dev")
ADDRESS_TYPES = ("residential", "mailing", "business")
FIRST_NAMES = (
    "Ana", "Marco", "John", "Maria", "Lia", "Peter", "Grace", "Noah", "Mina", "Jose",
    "Ben", "Kara", "Luca", "Leah", "Owen", "Rina", "Paolo", "Iris", "Nina", "Carl",
)
LAST_NAMES = (
    "Reyes", "Santos", "Cruz", "Garcia", "Mendoza", "Tan", "Lee", "Rivera", "Flores", "Navarro",
    "Delos Santos", "Ocampo", "Dela Cruz", "Villanueva", "King", "Hall", "Wright", "Lim", "Yu", "Chan",
)
STREET_NAMES = (
    "Mabini", "Rizal", "Ayala", "Bonifacio", "Sampaguita", "Acacia", "Orchid", "Harbor",
    "Pioneer", "Market", "Sunrise", "Northfield", "Lakeside", "Maple", "Central",
)
CITY_POOL = (
    ("Quezon City", "Metro Manila"),
    ("Makati", "Metro Manila"),
    ("Pasig", "Metro Manila"),
    ("Taguig", "Metro Manila"),
    ("Cebu City", "Cebu"),
    ("Davao City", "Davao del Sur"),
    ("Manila", "Metro Manila"),
    ("Iloilo City", "Iloilo"),
    ("Baguio", "Benguet"),
    ("Pasay", "Metro Manila"),
)
BANK_NAMES = (
    "Metro National Bank", "Pacific Union Bank", "Harbor Savings", "First Capital Bank",
    "Nexa Commercial Bank", "Summit Bank", "Global East Bank",
)
MERCHANT_NAMES = (
    "Acme Supplies", "Blue Harbor Retail", "Northwind Telecom", "Atlas Travel", "Luma Grocery",
    "Brightline Logistics", "Orchid Fashion", "Silver Peak Services", "Granite Health",
)
PROVIDERS = {
    "card": ("Visa", "Mastercard", "JCB", "UnionPay"),
    "bank_account": BANK_NAMES,
    "wallet": ("GCash", "PayMaya", "GrabPay", "SandboxWallet"),
    "cash": ("Cash Desk",),
}
FX_PAIR_CATALOG = (
    ("USD", "PHP"),
    ("PHP", "USD"),
    ("EUR", "USD"),
    ("USD", "EUR"),
    ("SGD", "USD"),
    ("USD", "SGD"),
    ("EUR", "PHP"),
    ("PHP", "EUR"),
    ("GBP", "USD"),
    ("AUD", "USD"),
)
FX_BASE_RATES = {
    ("USD", "PHP"): Decimal("56.1200000000"),
    ("PHP", "USD"): Decimal("0.0178200000"),
    ("EUR", "USD"): Decimal("1.0815000000"),
    ("USD", "EUR"): Decimal("0.9246000000"),
    ("SGD", "USD"): Decimal("0.7418000000"),
    ("USD", "SGD"): Decimal("1.3480000000"),
    ("EUR", "PHP"): Decimal("60.7200000000"),
    ("PHP", "EUR"): Decimal("0.0164700000"),
    ("GBP", "USD"): Decimal("1.2730000000"),
    ("AUD", "USD"): Decimal("0.6630000000"),
}
SYSTEM_ACCOUNT_SPECS = (
    {"role": "operating_cash", "category": "asset", "normal_balance": "debit", "name": "Operating Cash"},
    {"role": "settlement", "category": "asset", "normal_balance": "debit", "name": "Settlement Clearing"},
    {"role": "bank_clearing", "category": "asset", "normal_balance": "debit", "name": "Bank Clearing"},
    {"role": "card_clearing", "category": "asset", "normal_balance": "debit", "name": "Card Clearing"},
    {"role": "fees_income", "category": "revenue", "normal_balance": "credit", "name": "Fee Income"},
    {"role": "reserve", "category": "liability", "normal_balance": "credit", "name": "Liquidity Reserve"},
    {"role": "payable", "category": "liability", "normal_balance": "credit", "name": "External Payables"},
    {"role": "receivable", "category": "asset", "normal_balance": "debit", "name": "Receivables"},
    {"role": "suspense", "category": "liability", "normal_balance": "credit", "name": "Suspense Ledger"},
)
ORDER_TYPE_WEIGHTS = (
    ("card_charge", 24),
    ("bank_transfer", 16),
    ("wallet_transfer", 18),
    ("payout", 20),
    ("refund", 9),
    ("reversal", 5),
    ("adjustment", 8),
)


def load_dotenv(path: str | Path) -> dict[str, str]:
    values: dict[str, str] = {}
    env_path = Path(path)
    if not env_path.exists():
        return values
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def env_int(values: dict[str, str], key: str, default: int) -> int:
    raw = values.get(key)
    return int(raw) if raw else default


def to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def stable_int(*parts: Any) -> int:
    payload = ":".join(str(part) for part in parts).encode("utf-8")
    digest = hashlib.blake2b(payload, digest_size=8).digest()
    return int.from_bytes(digest, "big")


def stable_rng(seed: int, label: str, index: int) -> random.Random:
    return random.Random(stable_int(seed, label, index))


def deterministic_uuid(label: str, index: int) -> str:
    digest = hashlib.md5(f"{label}:{index}".encode("utf-8")).hexdigest()
    return str(uuid.UUID(digest))


def weighted_choice(rng: random.Random, pairs: Sequence[tuple[str, int]]) -> str:
    total = sum(weight for _, weight in pairs)
    pick = rng.uniform(0, total)
    running = 0.0
    for value, weight in pairs:
        running += weight
        if pick <= running:
            return value
    return pairs[-1][0]


def maybe(rng: random.Random, threshold: float) -> bool:
    return rng.random() < threshold


def clamp_amount(value: int, minimum: int = 100, maximum: int = 5_000_000) -> int:
    return max(minimum, min(value, maximum))


def compact_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def normalize_spaces(value: str, rng: random.Random) -> str:
    updated = value
    if maybe(rng, 0.10):
        updated = updated.replace(" ", "  ", 1)
    if maybe(rng, 0.04):
        updated = f" {updated}"
    if maybe(rng, 0.04):
        updated = f"{updated} "
    return updated


def messy_case(value: str, rng: random.Random) -> str:
    if maybe(rng, 0.04):
        return value.upper()
    if maybe(rng, 0.03):
        return value.lower()
    if maybe(rng, 0.05):
        return value.title()
    return value


def messy_email(first_name: str, last_name: str, domain: str, rng: random.Random) -> str:
    local = f"{first_name}.{last_name}".lower().replace(" ", "")
    if maybe(rng, 0.20):
        local = f"{local}+retry{rng.randint(1, 999)}"
    if maybe(rng, 0.12):
        local = local.replace(".", "_", 1)
    if maybe(rng, 0.05):
        local = local.upper()
    email = f"{local}@{domain}"
    if maybe(rng, 0.03):
        email = f"{email} "
    return email


def messy_phone(country_code: str, index: int, rng: random.Random) -> str:
    if country_code == "PH":
        base = f"917{(index * 37) % 10_000_000:07d}"
        options = (
            f"+63{base}",
            f"0{base}",
            f"+63-{base[:3]}-{base[3:6]}-{base[6:]}",
            f"+63 {base[:3]} {base[3:6]} {base[6:]}",
        )
    elif country_code == "US":
        area = 200 + (index % 600)
        line = 1000000 + (index * 91 % 9000000)
        options = (
            f"+1{area}{line}",
            f"+1-{area}-{str(line)[:3]}-{str(line)[3:]}",
            f"({area}) {str(line)[:3]}-{str(line)[3:]}",
        )
    else:
        line = 1_000_000 + (index * 73 % 8_000_000)
        options = (
            f"+{line}",
            f"+{str(line)[:2]} {str(line)[2:5]} {str(line)[5:]}",
        )
    phone = options[index % len(options)]
    if maybe(rng, 0.03):
        phone = f"{phone} ext {rng.randint(10, 999)}"
    return phone


def hash_value(*parts: Any) -> str:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def seeded_timestamp(
    seed: int,
    label: str,
    index: int,
    anchor: dt.datetime,
    lookback_days: int,
    min_offset_minutes: int = 0,
) -> dt.datetime:
    rng = stable_rng(seed, label, index)
    total_minutes = max(1, lookback_days * 24 * 60)
    offset = rng.randint(min_offset_minutes, total_minutes)
    return anchor - dt.timedelta(minutes=offset)


def jsonable_row(columns: Sequence[str], row: Sequence[Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, value in zip(columns, row):
        if isinstance(value, dt.datetime):
            payload[key] = value.isoformat()
        elif isinstance(value, dt.date):
            payload[key] = value.isoformat()
        elif isinstance(value, Decimal):
            payload[key] = str(value)
        else:
            payload[key] = value
    return payload


@dataclass(frozen=True)
class RowTargets:
    legal_entities: int
    customers: int
    counterparties: int
    fx_rate_days: int
    settlement_batches: int
    payment_orders: int

    @classmethod
    def from_scale(cls, scale: str, payment_orders_override: int | None = None) -> "RowTargets":
        presets = {
            "tiny": cls(legal_entities=2, customers=500, counterparties=80, fx_rate_days=14, settlement_batches=48, payment_orders=2_000),
            "small": cls(legal_entities=4, customers=10_000, counterparties=1_200, fx_rate_days=30, settlement_batches=320, payment_orders=50_000),
            "medium": cls(legal_entities=6, customers=50_000, counterparties=6_000, fx_rate_days=45, settlement_batches=1_500, payment_orders=250_000),
            "large": cls(legal_entities=8, customers=200_000, counterparties=25_000, fx_rate_days=60, settlement_batches=8_000, payment_orders=1_000_000),
            "xlarge": cls(legal_entities=12, customers=1_000_000, counterparties=120_000, fx_rate_days=90, settlement_batches=35_000, payment_orders=5_000_000),
        }
        if scale not in presets:
            raise ValueError(f"Unknown scale '{scale}'. Choose one of: {', '.join(sorted(presets))}")
        selected = presets[scale]
        if payment_orders_override is None:
            return selected
        ratio = max(payment_orders_override / selected.payment_orders, 0.02)
        return cls(
            legal_entities=selected.legal_entities,
            customers=max(500, int(selected.customers * ratio)),
            counterparties=max(selected.legal_entities * 50, int(selected.counterparties * ratio)),
            fx_rate_days=selected.fx_rate_days,
            settlement_batches=max(48, int(selected.settlement_batches * ratio)),
            payment_orders=payment_orders_override,
        )


@dataclass(frozen=True)
class LoaderConfig:
    env_file: Path
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    db_schema: str
    batch_size: int
    preview_rows: int
    seed: int
    scale: str
    dry_run: bool
    truncate: bool
    only_table: str | None
    row_targets: RowTargets

    @property
    def dsn(self) -> str:
        return (
            f"host={self.db_host} "
            f"port={self.db_port} "
            f"dbname={self.db_name} "
            f"user={self.db_user} "
            f"password={self.db_password}"
        )

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "LoaderConfig":
        env_values = load_dotenv(args.env_file)
        scale = args.scale or env_values.get("LOAD_SCALE", "small")
        payment_orders_override = args.payment_orders or env_int(env_values, "LOAD_PAYMENT_ORDERS", 0) or None
        return cls(
            env_file=Path(args.env_file),
            db_host=args.db_host or env_values.get("DB_HOST", "localhost"),
            db_port=int(args.db_port or env_values.get("DB_PORT", "5432")),
            db_name=args.db_name or env_values.get("DB_NAME", "financial_training"),
            db_user=args.db_user or env_values.get("DB_USER", "postgres"),
            db_password=args.db_password or env_values.get("DB_PASSWORD", "postgres"),
            db_schema=args.db_schema or env_values.get("DB_SCHEMA", "fintrain"),
            batch_size=int(args.batch_size or env_values.get("LOAD_BATCH_SIZE", "2000")),
            preview_rows=int(args.preview_rows or env_values.get("LOAD_PREVIEW_ROWS", "5")),
            seed=int(args.seed or env_values.get("LOAD_SEED", "20260417")),
            scale=scale,
            dry_run=args.dry_run or to_bool(env_values.get("LOAD_DRY_RUN"), False),
            truncate=args.truncate or to_bool(env_values.get("LOAD_TRUNCATE"), False),
            only_table=args.only,
            row_targets=RowTargets.from_scale(scale, payment_orders_override),
        )


class TableModule:
    name: str = ""
    columns: tuple[str, ...] = ()

    def row_count(self, state: "LoadState") -> int | None:
        return None

    def iter_rows(self, state: "LoadState") -> Iterator[Sequence[Any]]:
        raise NotImplementedError

    def project(self, payload: dict[str, Any]) -> tuple[Any, ...]:
        return tuple(payload.get(column) for column in self.columns)


class Database:
    def __init__(self, config: LoaderConfig) -> None:
        self.config = config
        self._driver = None
        self._connection = None

    def __enter__(self) -> "Database":
        try:
            import psycopg as driver
        except ImportError:
            try:
                import psycopg2 as driver
            except ImportError as exc:
                raise RuntimeError(
                    "Neither psycopg (v3) nor psycopg2 is installed. Install the dependency in requirements.txt first."
                ) from exc
        self._driver = driver
        self._connection = driver.connect(self.config.dsn)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._connection is None:
            return
        if exc_type is None:
            self._connection.commit()
        else:
            self._connection.rollback()
        self._connection.close()

    def truncate_tables(self, tables: Sequence[str]) -> None:
        if self._connection is None:
            raise RuntimeError("Database connection is not open.")
        qualified = ", ".join(f'"{self.config.db_schema}"."{table}"' for table in tables)
        sql = f"TRUNCATE TABLE {qualified} RESTART IDENTITY CASCADE"
        with self._connection.cursor() as cursor:
            cursor.execute(sql)
        self._connection.commit()

    def insert_rows(self, table: str, columns: Sequence[str], rows: Sequence[Sequence[Any]]) -> int:
        if not rows:
            return 0
        if self._connection is None:
            raise RuntimeError("Database connection is not open.")
        column_sql = ", ".join(f'"{column}"' for column in columns)
        placeholder = "(" + ", ".join(["%s"] * len(columns)) + ")"
        values_sql = ", ".join(placeholder for _ in rows)
        sql = f'INSERT INTO "{self.config.db_schema}"."{table}" ({column_sql}) VALUES {values_sql}'
        flat_values = list(chain.from_iterable(rows))
        with self._connection.cursor() as cursor:
            cursor.execute(sql, flat_values)
        self._connection.commit()
        return len(rows)


@dataclass(frozen=True)
class LoadState:
    config: LoaderConfig

    def __post_init__(self) -> None:
        object.__setattr__(self, "tz", dt.timezone(dt.timedelta(hours=8)))
        object.__setattr__(self, "anchor", dt.datetime(2026, 4, 17, 18, 0, tzinfo=self.tz))
        object.__setattr__(self, "system_account_count", len(SYSTEM_ACCOUNT_SPECS) * self.config.row_targets.legal_entities)
        object.__setattr__(
            self,
            "counterparty_block_size",
            max(1, self.counts.counterparties // self.counts.legal_entities),
        )
        role_map = {spec["role"]: index for index, spec in enumerate(SYSTEM_ACCOUNT_SPECS)}
        object.__setattr__(self, "system_role_index", role_map)
        pair_map: dict[str, list[int]] = {}
        for index, (from_code, _) in enumerate(FX_PAIR_CATALOG):
            pair_map.setdefault(from_code, []).append(index)
        object.__setattr__(self, "fx_pair_map", pair_map)

    @property
    def counts(self) -> RowTargets:
        return self.config.row_targets

    @property
    def total_accounts(self) -> int:
        return self.system_account_count + self.counts.customers

    @property
    def total_fx_rates(self) -> int:
        return len(FX_PAIR_CATALOG) * self.counts.fx_rate_days

    def currency_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for raw in CURRENCY_ROWS:
            created_at = self.anchor - dt.timedelta(days=3650)
            rows.append(
                {
                    **raw,
                    "is_active": True,
                    "created_at": created_at,
                }
            )
        return rows

    def legal_entity_id(self, index: int) -> str:
        return deterministic_uuid("legal_entity", index)

    def customer_id(self, index: int) -> str:
        return deterministic_uuid("customer", index)

    def customer_no(self, index: int) -> str:
        return f"CUST-{index + 1:09d}"

    def counterparty_id(self, index: int) -> str:
        return deterministic_uuid("counterparty", index)

    def payment_method_id(self, index: int) -> str:
        return deterministic_uuid("payment_method", index)

    def payment_order_id(self, index: int) -> str:
        return deterministic_uuid("payment_order", index)

    def settlement_batch_id(self, index: int) -> str:
        return deterministic_uuid("settlement_batch", index)

    def authorization_hold_id(self, index: int) -> str:
        return deterministic_uuid("authorization_hold", index)

    def journal_entry_id(self, index: int) -> str:
        return deterministic_uuid("journal_entry", index)

    def journal_entry_line_id(self, index: int, line_no: int) -> str:
        return deterministic_uuid(f"journal_entry_line:{line_no}", index)

    def customer_address_id(self, index: int) -> str:
        return deterministic_uuid("customer_address", index)

    def customer_identity_id(self, index: int) -> str:
        return deterministic_uuid("customer_identity", index)

    def fx_rate_id(self, index: int) -> str:
        return deterministic_uuid("fx_rate", index)

    def account_id(self, index: int) -> str:
        return deterministic_uuid("account", index)

    def wallet_account_id(self, customer_index: int) -> str:
        return self.account_id(self.system_account_count + customer_index)

    def system_account_id(self, entity_index: int, role: str) -> str:
        spec_index = self.system_role_index[role]
        return self.account_id(entity_index * len(SYSTEM_ACCOUNT_SPECS) + spec_index)

    def entity_currency(self, entity_index: int) -> str:
        return BASE_ENTITY_CURRENCIES[entity_index % len(BASE_ENTITY_CURRENCIES)]

    def entity_country(self, entity_index: int) -> str:
        return COUNTRY_BY_CURRENCY[self.entity_currency(entity_index)]

    def legal_entity_snapshot(self, index: int) -> dict[str, Any]:
        rng = stable_rng(self.config.seed, "legal_entities", index)
        currency = self.entity_currency(index)
        country = self.entity_country(index)
        created_at = seeded_timestamp(self.config.seed, "legal_entity_created", index, self.anchor, 2200)
        entity_kind = ("platform", "merchant", "bank", "processor", "branch")[index % 5]
        display_name = f"{country} {entity_kind.replace('_', ' ').title()} {index + 1}"
        return {
            "id": self.legal_entity_id(index),
            "entity_code": f"LE-{country}-{index + 1:04d}",
            "legal_name": normalize_spaces(f"{display_name} Holdings Ltd.", rng),
            "display_name": messy_case(display_name, rng),
            "entity_type": entity_kind,
            "country_code": country,
            "base_currency_code": currency,
            "status": "suspended" if index % 29 == 0 else "active",
            "created_at": created_at,
            "updated_at": created_at + dt.timedelta(days=index % 30, minutes=index % 77),
        }

    def customer_entity_index(self, customer_index: int) -> int:
        return customer_index % self.counts.legal_entities

    def customer_snapshot(self, index: int) -> dict[str, Any]:
        rng = stable_rng(self.config.seed, "customers", index)
        entity_index = self.customer_entity_index(index)
        first_name = FIRST_NAMES[index % len(FIRST_NAMES)]
        last_name = LAST_NAMES[(index * 7) % len(LAST_NAMES)]
        customer_type = "business" if index % 11 == 0 else "individual"
        status = weighted_choice(
            rng,
            (
                ("active", 78),
                ("pending_review", 7),
                ("restricted", 9),
                ("closed", 6),
            ),
        )
        created_at = seeded_timestamp(self.config.seed, "customer_created", index, self.anchor, 1100)
        email = None if maybe(rng, 0.09) else messy_email(first_name, last_name, EMAIL_DOMAINS[index % len(EMAIL_DOMAINS)], rng)
        phone = None if maybe(rng, 0.08) else messy_phone(self.entity_country(entity_index), index, rng)
        if customer_type == "business":
            first_name = normalize_spaces(f"{last_name} {('Trading', 'Logistics', 'Tech', 'Foods')[index % 4]}", rng)
            last_name = None
            birth_date = None
        else:
            first_name = normalize_spaces(first_name, rng)
            last_name = normalize_spaces(last_name, rng)
            age = 20 + (index % 42)
            birth_date = (self.anchor - dt.timedelta(days=age * 365 + index % 250)).date()
        return {
            "id": self.customer_id(index),
            "customer_no": self.customer_no(index),
            "legal_entity_id": self.legal_entity_id(entity_index),
            "customer_type": customer_type,
            "status": status,
            "email": email,
            "phone": phone,
            "first_name": messy_case(first_name, rng),
            "last_name": None if last_name is None else messy_case(last_name, rng),
            "birth_date": birth_date,
            "created_at": created_at,
            "updated_at": created_at + dt.timedelta(days=index % 14, minutes=index % 180),
        }

    def customer_address_snapshot(self, index: int) -> dict[str, Any]:
        rng = stable_rng(self.config.seed, "customer_addresses", index)
        entity_country = self.entity_country(self.customer_entity_index(index))
        city, region = CITY_POOL[index % len(CITY_POOL)]
        building = 10 + (index * 13) % 9900
        line1 = normalize_spaces(f"{building} {STREET_NAMES[index % len(STREET_NAMES)]} Street", rng)
        line2 = None
        if maybe(rng, 0.25):
            line2 = normalize_spaces(f"Unit {1 + index % 1204}", rng)
        postal_code = None if maybe(rng, 0.12) else f"{1000 + (index % 8500):04d}"
        return {
            "id": self.customer_address_id(index),
            "customer_id": self.customer_id(index),
            "address_type": ADDRESS_TYPES[index % len(ADDRESS_TYPES)] if index % 9 == 0 else "residential",
            "line1": line1,
            "line2": line2,
            "city": messy_case(city, rng),
            "region": None if maybe(rng, 0.08) else region,
            "postal_code": postal_code,
            "country_code": entity_country,
            "is_primary": True,
            "created_at": seeded_timestamp(self.config.seed, "customer_address_created", index, self.anchor, 1050),
        }

    def customer_identity_snapshot(self, index: int) -> dict[str, Any]:
        rng = stable_rng(self.config.seed, "customer_identities", index)
        customer = self.customer_snapshot(index)
        customer_type = customer["customer_type"]
        if customer_type == "business":
            identity_type = "business_registration"
        else:
            identity_type = ("passport", "national_id", "drivers_license", "tin")[index % 4]
        status = weighted_choice(rng, (("verified", 68), ("received", 14), ("rejected", 8), ("expired", 10)))
        verified_at = None
        created_at = seeded_timestamp(self.config.seed, "customer_identity_created", index, self.anchor, 1000)
        if status == "verified":
            verified_at = created_at + dt.timedelta(days=1 + index % 6, hours=index % 5)
        return {
            "id": self.customer_identity_id(index),
            "customer_id": customer["id"],
            "identity_type": identity_type,
            "issuing_country_code": self.entity_country(self.customer_entity_index(index)),
            "id_number_hash": hash_value(identity_type, customer["customer_no"]),
            "status": status,
            "verified_at": verified_at,
            "created_at": created_at,
        }

    def counterparty_entity_index(self, index: int) -> int:
        block_start = index // self.counterparty_block_size
        return min(self.counts.legal_entities - 1, block_start)

    def counterparty_snapshot(self, index: int) -> dict[str, Any]:
        rng = stable_rng(self.config.seed, "counterparties", index)
        entity_index = self.counterparty_entity_index(index)
        counterparty_type = weighted_choice(rng, (("bank", 28), ("merchant", 34), ("business", 18), ("individual", 20)))
        country = COUNTRY_POOL[index % len(COUNTRY_POOL)]
        if counterparty_type == "bank":
            display_name = BANK_NAMES[index % len(BANK_NAMES)]
            bank_name = display_name
            masked_account = f"****{1000 + (index * 17) % 9000}"
        elif counterparty_type == "merchant":
            display_name = MERCHANT_NAMES[index % len(MERCHANT_NAMES)]
            bank_name = None
            masked_account = None
        elif counterparty_type == "business":
            display_name = f"{LAST_NAMES[index % len(LAST_NAMES)]} {('Holdings', 'Trading', 'Ventures')[index % 3]}"
            bank_name = None
            masked_account = None
        else:
            display_name = f"{FIRST_NAMES[index % len(FIRST_NAMES)]} {LAST_NAMES[(index * 5) % len(LAST_NAMES)]}"
            bank_name = None
            masked_account = None
        created_at = seeded_timestamp(self.config.seed, "counterparty_created", index, self.anchor, 1300)
        return {
            "id": self.counterparty_id(index),
            "legal_entity_id": self.legal_entity_id(entity_index),
            "counterparty_code": f"CP-{entity_index + 1:03d}-{index + 1:08d}",
            "counterparty_type": counterparty_type,
            "display_name": normalize_spaces(messy_case(display_name, rng), rng),
            "country_code": country,
            "bank_name": bank_name,
            "bank_account_masked": masked_account,
            "external_reference": f"ext-{index + 1:010d}" if index % 7 else f"legacy/{index + 1:08d}",
            "status": weighted_choice(rng, (("active", 84), ("blocked", 8), ("inactive", 8))),
            "created_at": created_at,
            "updated_at": created_at + dt.timedelta(days=index % 10, minutes=index % 50),
        }

    def payment_method_snapshot(self, index: int) -> dict[str, Any]:
        rng = stable_rng(self.config.seed, "payment_methods", index)
        entity_country = self.entity_country(self.customer_entity_index(index))
        method_type = weighted_choice(rng, (("card", 45), ("bank_account", 35), ("wallet", 18), ("cash", 2)))
        provider_name = PROVIDERS[method_type][index % len(PROVIDERS[method_type])]
        expiry_month = None
        expiry_year = None
        status = weighted_choice(rng, (("active", 77), ("pending_verification", 7), ("suspended", 6), ("expired", 7), ("revoked", 3)))
        if method_type == "card":
            expiry_month = 1 + (index % 12)
            expiry_year = 2024 + (index % 8)
            masked_identifier = f"4{1000 + (index % 9000):04d}******{1000 + (index * 3) % 9000:04d}"
        elif method_type == "bank_account":
            prefix = entity_country
            masked_identifier = f"{prefix}{10 + index % 90}********{1000 + (index * 7) % 9000:04d}"
        elif method_type == "wallet":
            masked_identifier = f"wallet::{self.customer_no(index)}"
        else:
            masked_identifier = f"cash-desk-{index % 250:03d}"
        created_at = seeded_timestamp(self.config.seed, "payment_method_created", index, self.anchor, 950)
        return {
            "id": self.payment_method_id(index),
            "customer_id": self.customer_id(index),
            "method_type": method_type,
            "provider_name": provider_name,
            "token_ref": f"tok_{index + 1:012d}",
            "masked_identifier": masked_identifier,
            "expiry_month": expiry_month,
            "expiry_year": expiry_year,
            "status": status,
            "is_default": index % 5 != 0,
            "created_at": created_at,
            "updated_at": created_at + dt.timedelta(days=index % 8, minutes=index % 33),
        }

    def account_snapshot(self, index: int) -> dict[str, Any]:
        if index < self.system_account_count:
            entity_index = index // len(SYSTEM_ACCOUNT_SPECS)
            spec = SYSTEM_ACCOUNT_SPECS[index % len(SYSTEM_ACCOUNT_SPECS)]
            created_at = seeded_timestamp(self.config.seed, "system_account_created", index, self.anchor, 1600)
            return {
                "id": self.account_id(index),
                "account_no": f"SYS-{entity_index + 1:03d}-{index % len(SYSTEM_ACCOUNT_SPECS) + 1:02d}",
                "legal_entity_id": self.legal_entity_id(entity_index),
                "customer_id": None,
                "parent_account_id": None,
                "account_name": f"{spec['name']} - {self.entity_currency(entity_index)}",
                "account_category": spec["category"],
                "account_role": spec["role"],
                "normal_balance": spec["normal_balance"],
                "currency_code": self.entity_currency(entity_index),
                "status": "closed" if index % 97 == 0 else "active",
                "allow_overdraft": spec["role"] in {"settlement", "receivable", "suspense"},
                "created_at": created_at,
                "updated_at": created_at + dt.timedelta(days=index % 40, minutes=index % 90),
            }
        customer_index = index - self.system_account_count
        customer = self.customer_snapshot(customer_index)
        created_at = seeded_timestamp(self.config.seed, "wallet_account_created", customer_index, self.anchor, 1000)
        name_bits = [customer["first_name"] or "Customer", customer["last_name"] or ""]
        display = normalize_spaces(" ".join(bit for bit in name_bits if bit), stable_rng(self.config.seed, "wallet_account_name", customer_index))
        return {
            "id": self.wallet_account_id(customer_index),
            "account_no": f"WAL-{customer_index + 1:010d}",
            "legal_entity_id": customer["legal_entity_id"],
            "customer_id": customer["id"],
            "parent_account_id": None,
            "account_name": f"{display} Wallet - {self.entity_currency(self.customer_entity_index(customer_index))}",
            "account_category": "liability",
            "account_role": "customer_wallet",
            "normal_balance": "credit",
            "currency_code": self.entity_currency(self.customer_entity_index(customer_index)),
            "status": "frozen" if customer_index % 113 == 0 else "active",
            "allow_overdraft": customer_index % 101 == 0,
            "created_at": created_at,
            "updated_at": created_at + dt.timedelta(days=customer_index % 21, minutes=customer_index % 120),
        }

    def fx_rate_snapshot(self, index: int) -> dict[str, Any]:
        day_index = index // len(FX_PAIR_CATALOG)
        pair_index = index % len(FX_PAIR_CATALOG)
        from_code, to_code = FX_PAIR_CATALOG[pair_index]
        rng = stable_rng(self.config.seed, "fx_rates", index)
        rate_date = (self.anchor.date() - dt.timedelta(days=day_index))
        drift = Decimal(str((rng.randint(-55, 55)) / 10000)).quantize(Decimal("0.0000000001"))
        rate = (FX_BASE_RATES[(from_code, to_code)] + drift).quantize(Decimal("0.0000000001"))
        captured_at = dt.datetime.combine(rate_date, dt.time(hour=8, minute=index % 59), tzinfo=self.tz)
        return {
            "id": self.fx_rate_id(index),
            "rate_date": rate_date,
            "from_currency_code": from_code,
            "to_currency_code": to_code,
            "provider_name": ("ECB Snapshot", "Reuters Tick", "Treasury Feed")[index % 3],
            "rate": rate,
            "captured_at": captured_at,
            "created_at": captured_at,
        }

    def settlement_batch_snapshot(self, index: int) -> dict[str, Any]:
        rng = stable_rng(self.config.seed, "settlement_batches", index)
        entity_index = index % self.counts.legal_entities
        start_at = self.anchor - dt.timedelta(hours=index % 24, days=index // max(1, self.counts.legal_entities))
        end_at = start_at + dt.timedelta(hours=4 + (index % 4))
        expected = clamp_amount(20_000 + (index * 791) % 8_000_000, minimum=10_000, maximum=25_000_000)
        status = weighted_choice(rng, (("open", 10), ("submitted", 12), ("settled", 56), ("failed", 8), ("reconciled", 14)))
        settled_amount = None if status in {"open", "submitted"} else max(0, expected - (index % 13) * 125)
        return {
            "id": self.settlement_batch_id(index),
            "batch_no": f"SB-{start_at:%Y%m%d}-{index + 1:08d}",
            "legal_entity_id": self.legal_entity_id(entity_index),
            "currency_code": self.entity_currency(entity_index),
            "settlement_account_id": self.system_account_id(entity_index, "settlement"),
            "batch_status": status,
            "window_start_at": start_at,
            "window_end_at": end_at,
            "expected_amount_minor": expected,
            "settled_amount_minor": settled_amount,
            "external_reference": f"bank-settle-{index + 1:010d}" if index % 6 else f"ops/manual/{index + 1:08d}",
            "created_at": start_at - dt.timedelta(minutes=20),
            "updated_at": end_at + dt.timedelta(minutes=index % 35),
        }

    def counterparty_index_for_order(self, entity_index: int, order_index: int) -> int:
        local_index = (order_index // self.counts.legal_entities) % self.counterparty_block_size
        return min(self.counts.counterparties - 1, entity_index * self.counterparty_block_size + local_index)

    def payment_order_snapshot(self, index: int) -> dict[str, Any]:
        rng = stable_rng(self.config.seed, "payment_orders", index)
        customer_index = index % self.counts.customers
        entity_index = self.customer_entity_index(customer_index)
        order_type = weighted_choice(rng, ORDER_TYPE_WEIGHTS)
        direction_map = {
            "card_charge": "inbound",
            "bank_transfer": "inbound",
            "wallet_transfer": "internal",
            "payout": "outbound",
            "refund": "internal",
            "reversal": "internal",
            "adjustment": "internal",
        }
        status_options = {
            "card_charge": (("pending_authorization", 8), ("authorized", 15), ("captured", 12), ("settled", 48), ("failed", 7), ("canceled", 3), ("refunded", 7)),
            "bank_transfer": (("created", 8), ("captured", 10), ("settled", 54), ("failed", 16), ("canceled", 5), ("reversed", 7)),
            "wallet_transfer": (("created", 4), ("captured", 10), ("settled", 60), ("failed", 10), ("canceled", 6), ("reversed", 10)),
            "payout": (("pending_authorization", 6), ("authorized", 10), ("captured", 11), ("settled", 48), ("failed", 17), ("canceled", 8)),
            "refund": (("created", 6), ("captured", 15), ("settled", 54), ("failed", 15), ("reversed", 10)),
            "reversal": (("created", 5), ("captured", 20), ("settled", 20), ("reversed", 55)),
            "adjustment": (("created", 6), ("captured", 14), ("settled", 52), ("failed", 10), ("canceled", 8), ("reversed", 10)),
        }
        status = weighted_choice(rng, status_options[order_type])
        customer = self.customer_snapshot(customer_index)
        base_amount = 2_500 + (index * 137) % 450_000
        if customer["customer_type"] == "business":
            base_amount *= 3
        amount_minor = clamp_amount(base_amount, maximum=3_500_000)
        fee_amount_minor = 0
        if order_type in {"card_charge", "bank_transfer", "wallet_transfer", "payout"}:
            fee_amount_minor = min(amount_minor // 4, max(0, (amount_minor * (20 + index % 60)) // 10_000))
        elif order_type == "adjustment" and index % 5 == 0:
            fee_amount_minor = min(amount_minor // 10, 1_500)
        requested_at = seeded_timestamp(self.config.seed, "payment_order_requested", index, self.anchor, 180)
        authorized_at = None
        captured_at = None
        completed_at = None
        if status in {"authorized", "captured", "settled", "failed", "refunded", "reversed"}:
            authorized_at = requested_at + dt.timedelta(minutes=1 + index % 45)
        if status in {"captured", "settled", "refunded", "reversed"}:
            captured_at = (authorized_at or requested_at) + dt.timedelta(minutes=1 + index % 80)
        if status in {"settled", "failed", "canceled", "refunded", "reversed"}:
            completed_at = (captured_at or authorized_at or requested_at) + dt.timedelta(minutes=5 + index % 720)
        source_account_id = None
        destination_account_id = None
        payment_method_id = None
        counterparty_id = None
        if order_type in {"card_charge", "bank_transfer"}:
            payment_method_id = self.payment_method_id(customer_index)
            destination_account_id = self.wallet_account_id(customer_index)
        elif order_type == "wallet_transfer":
            source_account_id = self.wallet_account_id(customer_index)
            destination_account_id = self.wallet_account_id((customer_index + 97) % self.counts.customers)
        elif order_type == "payout":
            source_account_id = self.wallet_account_id(customer_index)
            counterparty_id = self.counterparty_id(self.counterparty_index_for_order(entity_index, index))
        elif order_type == "refund":
            source_account_id = self.system_account_id(entity_index, "operating_cash")
            destination_account_id = self.wallet_account_id(customer_index)
        elif order_type == "reversal":
            source_account_id = self.system_account_id(entity_index, "suspense")
            destination_account_id = self.wallet_account_id(customer_index)
        else:
            if index % 2 == 0:
                source_account_id = self.system_account_id(entity_index, "reserve")
                destination_account_id = self.wallet_account_id(customer_index)
            else:
                source_account_id = self.wallet_account_id(customer_index)
                destination_account_id = self.system_account_id(entity_index, "reserve")
        settlement_batch_id = self.settlement_batch_id(index % self.counts.settlement_batches)
        currency_code = self.entity_currency(entity_index)
        fx_rate_id = None
        if currency_code in self.fx_pair_map and index % 6 == 0:
            pair_slot = self.fx_pair_map[currency_code][index % len(self.fx_pair_map[currency_code])]
            day_slot = index % self.counts.fx_rate_days
            fx_rate_id = self.fx_rate_id(day_slot * len(FX_PAIR_CATALOG) + pair_slot)
        description = normalize_spaces(
            f"{order_type.replace('_', ' ')} for {customer['customer_no']} ref {index + 1:08d}",
            rng,
        )
        if maybe(rng, 0.12):
            description = f"{description} / retry"
        return {
            "id": self.payment_order_id(index),
            "payment_order_no": f"PO-{requested_at:%Y%m%d}-{index + 1:09d}",
            "legal_entity_id": self.legal_entity_id(entity_index),
            "customer_id": None if order_type == "adjustment" and index % 40 == 0 else customer["id"],
            "source_account_id": source_account_id,
            "destination_account_id": destination_account_id,
            "payment_method_id": payment_method_id,
            "counterparty_id": counterparty_id,
            "settlement_batch_id": settlement_batch_id,
            "order_type": order_type,
            "direction": direction_map[order_type],
            "status": status,
            "amount_minor": amount_minor,
            "fee_amount_minor": fee_amount_minor,
            "currency_code": currency_code,
            "fx_rate_id": fx_rate_id,
            "idempotency_key": None if index % 17 == 0 else f"idem-{index + 1:012d}",
            "external_reference": None if index % 11 == 0 else f"ext-pay-{index + 1:010d}",
            "description": description,
            "requested_at": requested_at,
            "authorized_at": authorized_at,
            "captured_at": captured_at,
            "completed_at": completed_at,
            "created_at": requested_at,
            "updated_at": completed_at or captured_at or authorized_at or requested_at,
        }

    def payment_order_event_rows(self, index: int) -> list[dict[str, Any]]:
        order = self.payment_order_snapshot(index)
        rows: list[dict[str, Any]] = []
        rows.append(
            {
                "payment_order_id": order["id"],
                "event_type": "created",
                "from_status": None,
                "to_status": "created",
                "actor_type": "customer" if order["customer_id"] else "operator",
                "actor_reference": order["customer_id"] or f"ops-batch-{index % 80:03d}",
                "event_payload": compact_json({"channel": "api" if index % 3 else "ops_ui", "amount_minor": order["amount_minor"]}),
                "created_at": order["requested_at"],
            }
        )
        if order["status"] in {"pending_authorization", "authorized", "captured", "settled", "failed", "refunded", "reversed"}:
            rows.append(
                {
                    "payment_order_id": order["id"],
                    "event_type": "authorization_requested",
                    "from_status": "created",
                    "to_status": "pending_authorization",
                    "actor_type": "system",
                    "actor_reference": "risk-engine",
                    "event_payload": compact_json({"score": index % 100, "entity": order["legal_entity_id"]}),
                    "created_at": order["requested_at"] + dt.timedelta(seconds=30),
                }
            )
        if order["authorized_at"] is not None:
            previous = "pending_authorization" if len(rows) > 1 else "created"
            rows.append(
                {
                    "payment_order_id": order["id"],
                    "event_type": "authorized",
                    "from_status": previous,
                    "to_status": "authorized",
                    "actor_type": "system",
                    "actor_reference": "payments-core",
                    "event_payload": compact_json({"risk_band": ("low", "medium", "high")[index % 3]}),
                    "created_at": order["authorized_at"],
                }
            )
        if order["captured_at"] is not None:
            rows.append(
                {
                    "payment_order_id": order["id"],
                    "event_type": "captured",
                    "from_status": "authorized",
                    "to_status": "captured",
                    "actor_type": "system",
                    "actor_reference": "ledger-bridge",
                    "event_payload": compact_json({"captured_amount_minor": order["amount_minor"]}),
                    "created_at": order["captured_at"],
                }
            )
        terminal_map = {
            "settled": "settled",
            "failed": "failed",
            "canceled": "canceled",
            "refunded": "refunded",
            "reversed": "reversed",
        }
        if order["status"] in terminal_map and order["completed_at"] is not None:
            rows.append(
                {
                    "payment_order_id": order["id"],
                    "event_type": terminal_map[order["status"]],
                    "from_status": "captured" if order["captured_at"] else "created",
                    "to_status": order["status"],
                    "actor_type": "webhook" if order["status"] == "settled" else "system",
                    "actor_reference": "bank-webhook" if order["status"] == "settled" else "payments-core",
                    "event_payload": compact_json({"final_status": order["status"], "external_reference": order["external_reference"]}),
                    "created_at": order["completed_at"],
                }
            )
        if index % 29 == 0:
            rows.append(
                {
                    "payment_order_id": order["id"],
                    "event_type": "note_added",
                    "from_status": order["status"],
                    "to_status": order["status"],
                    "actor_type": "operator",
                    "actor_reference": f"case-{index % 1400:04d}",
                    "event_payload": compact_json({"note": "manual_review", "reason_code": f"MR{index % 17:02d}"}),
                    "created_at": (order["completed_at"] or order["updated_at"]) + dt.timedelta(minutes=10),
                }
            )
        return rows

    def authorization_hold_snapshot(self, index: int) -> dict[str, Any] | None:
        order = self.payment_order_snapshot(index)
        if order["order_type"] not in {"card_charge", "payout", "wallet_transfer"}:
            return None
        if order["status"] == "created":
            return None
        account_id = order["source_account_id"] or order["destination_account_id"]
        if account_id is None:
            return None
        created_at = order["requested_at"] + dt.timedelta(seconds=15)
        expires_at = created_at + dt.timedelta(days=2)
        hold_status = "active"
        released_at = None
        captured_at = None
        if order["status"] in {"failed", "canceled", "reversed"}:
            hold_status = "released"
            released_at = order["completed_at"] or order["updated_at"]
        elif order["status"] in {"captured", "settled", "refunded"}:
            hold_status = "captured"
            captured_at = order["captured_at"] or order["updated_at"]
        elif order["status"] == "authorized":
            hold_status = "active"
        if index % 91 == 0 and hold_status == "active":
            hold_status = "expired"
            expires_at = created_at + dt.timedelta(hours=6)
        return {
            "id": self.authorization_hold_id(index),
            "payment_order_id": order["id"],
            "account_id": account_id,
            "currency_code": order["currency_code"],
            "amount_minor": order["amount_minor"],
            "hold_status": hold_status,
            "expires_at": expires_at,
            "released_at": released_at,
            "captured_at": captured_at,
            "created_at": created_at,
            "updated_at": captured_at or released_at or max(created_at, expires_at),
        }

    def order_has_journal_entry(self, index: int) -> bool:
        order = self.payment_order_snapshot(index)
        if order["status"] not in {"captured", "settled", "refunded", "reversed"}:
            return False
        return index % 17 != 0

    def journal_entry_snapshot(self, index: int) -> dict[str, Any] | None:
        if not self.order_has_journal_entry(index):
            return None
        order = self.payment_order_snapshot(index)
        effective_at = order["captured_at"] or order["authorized_at"] or order["requested_at"]
        if order["status"] == "captured" and index % 7 == 0:
            status = "draft"
            posted_at = None
        elif order["status"] == "reversed":
            status = "reversed"
            posted_at = order["completed_at"] or effective_at
        else:
            status = "posted"
            posted_at = order["completed_at"] or effective_at
        reversal_of_entry_id = None
        if order["status"] == "reversed" and index > 0 and self.order_has_journal_entry(index - 1):
            reversal_of_entry_id = self.journal_entry_id(index - 1)
        return {
            "id": self.journal_entry_id(index),
            "entry_no": f"JE-{effective_at:%Y%m%d}-{index + 1:09d}",
            "legal_entity_id": order["legal_entity_id"],
            "payment_order_id": order["id"],
            "entry_type": "reversal" if order["status"] == "reversed" else ("refund" if order["order_type"] == "refund" else "payment"),
            "status": status,
            "effective_at": effective_at,
            "posted_at": posted_at,
            "reversal_of_entry_id": reversal_of_entry_id,
            "description": f"{order['order_type'].replace('_', ' ')} journal for {order['payment_order_no']}",
            "created_at": effective_at,
            "updated_at": posted_at or effective_at,
        }

    def journal_line_rows(self, index: int) -> list[dict[str, Any]]:
        entry = self.journal_entry_snapshot(index)
        if entry is None:
            return []
        order = self.payment_order_snapshot(index)
        entity_index = self.customer_entity_index(index % self.counts.customers)
        gross_amount = order["amount_minor"]
        fee_amount = order["fee_amount_minor"]
        net_amount = gross_amount - fee_amount
        if order["source_account_id"] is None and order["payment_method_id"] is not None:
            debit_account = self.system_account_id(entity_index, "operating_cash")
        else:
            debit_account = order["source_account_id"] or self.system_account_id(entity_index, "suspense")
        if order["destination_account_id"] is not None:
            credit_account = order["destination_account_id"]
        elif order["counterparty_id"] is not None:
            credit_account = self.system_account_id(entity_index, "operating_cash")
        else:
            credit_account = self.system_account_id(entity_index, "suspense")
        created_at = entry["effective_at"]
        rows = [
            {
                "id": self.journal_entry_line_id(index, 1),
                "journal_entry_id": entry["id"],
                "line_no": 1,
                "account_id": debit_account,
                "entry_side": "debit",
                "amount_minor": gross_amount,
                "currency_code": order["currency_code"],
                "memo": "Gross amount leg",
                "created_at": created_at,
            }
        ]
        rows.append(
            {
                "id": self.journal_entry_line_id(index, 2),
                "journal_entry_id": entry["id"],
                "line_no": 2,
                "account_id": credit_account,
                "entry_side": "credit",
                "amount_minor": net_amount,
                "currency_code": order["currency_code"],
                "memo": "Net settlement leg",
                "created_at": created_at,
            }
        )
        if fee_amount > 0:
            rows.append(
                {
                    "id": self.journal_entry_line_id(index, 3),
                    "journal_entry_id": entry["id"],
                    "line_no": 3,
                    "account_id": self.system_account_id(entity_index, "fees_income"),
                    "entry_side": "credit",
                    "amount_minor": fee_amount,
                    "currency_code": order["currency_code"],
                    "memo": "Fee income leg",
                    "created_at": created_at,
                }
            )
        return rows

    def account_balance_snapshot(self, index: int) -> dict[str, Any]:
        account = self.account_snapshot(index)
        rng = stable_rng(self.config.seed, "account_balances", index)
        version = 1 + (index % 99)
        if account["account_role"] == "customer_wallet":
            posted = -clamp_amount(2_000 + (index * 43) % 850_000, maximum=2_000_000)
            pending_inflow = 0 if index % 7 else 500 + (index % 19) * 100
            pending_outflow = 0 if index % 5 else 1_000 + (index % 23) * 200
        else:
            role = account["account_role"]
            if role in {"operating_cash", "settlement", "bank_clearing", "card_clearing", "receivable"}:
                posted = clamp_amount(50_000 + (index * 997) % 9_500_000, maximum=250_000_000)
            else:
                posted = -clamp_amount(20_000 + (index * 541) % 4_000_000, maximum=150_000_000)
            pending_inflow = 0 if maybe(rng, 0.80) else clamp_amount(100 + (index * 31) % 40_000, maximum=500_000)
            pending_outflow = 0 if maybe(rng, 0.75) else clamp_amount(100 + (index * 17) % 35_000, maximum=500_000)
        return {
            "account_id": account["id"],
            "posted_balance_minor": posted,
            "pending_inflow_minor": pending_inflow,
            "pending_outflow_minor": pending_outflow,
            "balance_version": version,
            "updated_at": account["updated_at"] + dt.timedelta(minutes=index % 300),
        }


def max_batch_for_columns(configured_batch_size: int, column_count: int) -> int:
    if column_count <= 0:
        return configured_batch_size
    pg_parameter_limit = 65535
    safe_limit = max(1, (pg_parameter_limit // column_count) - 1)
    return max(1, min(configured_batch_size, safe_limit))
