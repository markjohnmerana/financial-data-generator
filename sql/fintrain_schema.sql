

CREATE SCHEMA IF NOT EXISTS fintrain;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

SET search_path TO fintrain, public;

CREATE OR REPLACE FUNCTION fintrain.set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

CREATE TABLE IF NOT EXISTS currencies (
    code varchar(3) PRIMARY KEY,
    numeric_code varchar(3) NOT NULL UNIQUE,
    name text NOT NULL,
    minor_unit smallint NOT NULL CHECK (minor_unit BETWEEN 0 AND 4),
    symbol text,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (code = upper(code)),
    CHECK (numeric_code ~ '^[0-9]{3}$')
);

CREATE TABLE IF NOT EXISTS legal_entities (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_code varchar(40) NOT NULL UNIQUE,
    legal_name text NOT NULL,
    display_name text NOT NULL,
    entity_type varchar(20) NOT NULL CHECK (entity_type IN ('platform', 'merchant', 'bank', 'processor', 'branch')),
    country_code varchar(2) NOT NULL CHECK (country_code ~ '^[A-Z]{2}$'),
    base_currency_code varchar(3) NOT NULL REFERENCES currencies(code),
    status varchar(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'closed')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS customers (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_no varchar(40) NOT NULL UNIQUE,
    legal_entity_id uuid NOT NULL REFERENCES legal_entities(id),
    customer_type varchar(20) NOT NULL CHECK (customer_type IN ('individual', 'business')),
    status varchar(20) NOT NULL DEFAULT 'active' CHECK (status IN ('pending_review', 'active', 'restricted', 'closed')),
    email text,
    phone text,
    first_name text,
    last_name text,
    birth_date date,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS customer_addresses (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id uuid NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    address_type varchar(20) NOT NULL CHECK (address_type IN ('residential', 'mailing', 'business')),
    line1 text NOT NULL,
    line2 text,
    city text NOT NULL,
    region text,
    postal_code text,
    country_code varchar(2) NOT NULL CHECK (country_code ~ '^[A-Z]{2}$'),
    is_primary boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS customer_identities (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id uuid NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    identity_type varchar(30) NOT NULL CHECK (identity_type IN ('passport', 'national_id', 'drivers_license', 'tin', 'business_registration')),
    issuing_country_code varchar(2) NOT NULL CHECK (issuing_country_code ~ '^[A-Z]{2}$'),
    id_number_hash char(64) NOT NULL,
    status varchar(20) NOT NULL DEFAULT 'received' CHECK (status IN ('received', 'verified', 'rejected', 'expired')),
    verified_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (identity_type, issuing_country_code, id_number_hash)
);

CREATE TABLE IF NOT EXISTS counterparties (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    legal_entity_id uuid NOT NULL REFERENCES legal_entities(id),
    counterparty_code varchar(40) NOT NULL UNIQUE,
    counterparty_type varchar(20) NOT NULL CHECK (counterparty_type IN ('individual', 'business', 'bank', 'merchant')),
    display_name text NOT NULL,
    country_code varchar(2) NOT NULL CHECK (country_code ~ '^[A-Z]{2}$'),
    bank_name text,
    bank_account_masked text,
    external_reference text,
    status varchar(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'blocked', 'inactive')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS payment_methods (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id uuid NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    method_type varchar(20) NOT NULL CHECK (method_type IN ('card', 'bank_account', 'wallet', 'cash')),
    provider_name text NOT NULL,
    token_ref text NOT NULL UNIQUE,
    masked_identifier text NOT NULL,
    expiry_month smallint,
    expiry_year integer,
    status varchar(20) NOT NULL DEFAULT 'active' CHECK (status IN ('pending_verification', 'active', 'suspended', 'expired', 'revoked')),
    is_default boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (
        (expiry_month IS NULL AND expiry_year IS NULL)
        OR (expiry_month BETWEEN 1 AND 12 AND expiry_year >= 2024)
    )
);

CREATE TABLE IF NOT EXISTS accounts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    account_no varchar(40) NOT NULL UNIQUE,
    legal_entity_id uuid NOT NULL REFERENCES legal_entities(id),
    customer_id uuid REFERENCES customers(id),
    parent_account_id uuid REFERENCES accounts(id),
    account_name text NOT NULL,
    account_category varchar(20) NOT NULL CHECK (account_category IN ('asset', 'liability', 'equity', 'revenue', 'expense', 'off_balance')),
    account_role varchar(20) NOT NULL CHECK (account_role IN ('customer_wallet', 'operating_cash', 'bank_clearing', 'card_clearing', 'settlement', 'fees_income', 'reserve', 'payable', 'receivable', 'suspense')),
    normal_balance varchar(10) NOT NULL CHECK (normal_balance IN ('debit', 'credit')),
    currency_code varchar(3) NOT NULL REFERENCES currencies(code),
    status varchar(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'frozen', 'closed')),
    allow_overdraft boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS account_balances (
    account_id uuid PRIMARY KEY REFERENCES accounts(id) ON DELETE CASCADE,
    posted_balance_minor bigint NOT NULL DEFAULT 0,
    pending_inflow_minor bigint NOT NULL DEFAULT 0 CHECK (pending_inflow_minor >= 0),
    pending_outflow_minor bigint NOT NULL DEFAULT 0 CHECK (pending_outflow_minor >= 0),
    available_balance_minor bigint GENERATED ALWAYS AS (posted_balance_minor + pending_inflow_minor - pending_outflow_minor) STORED,
    balance_version bigint NOT NULL DEFAULT 0 CHECK (balance_version >= 0),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fx_rates (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    rate_date date NOT NULL,
    from_currency_code varchar(3) NOT NULL REFERENCES currencies(code),
    to_currency_code varchar(3) NOT NULL REFERENCES currencies(code),
    provider_name text NOT NULL,
    rate numeric(20,10) NOT NULL CHECK (rate > 0),
    captured_at timestamptz NOT NULL DEFAULT now(),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (rate_date, from_currency_code, to_currency_code, provider_name),
    CHECK (from_currency_code <> to_currency_code)
);

CREATE TABLE IF NOT EXISTS settlement_batches (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_no varchar(40) NOT NULL UNIQUE,
    legal_entity_id uuid NOT NULL REFERENCES legal_entities(id),
    currency_code varchar(3) NOT NULL REFERENCES currencies(code),
    settlement_account_id uuid NOT NULL REFERENCES accounts(id),
    batch_status varchar(20) NOT NULL DEFAULT 'open' CHECK (batch_status IN ('open', 'submitted', 'settled', 'failed', 'reconciled')),
    window_start_at timestamptz NOT NULL,
    window_end_at timestamptz NOT NULL,
    expected_amount_minor bigint NOT NULL DEFAULT 0,
    settled_amount_minor bigint,
    external_reference text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (window_end_at >= window_start_at),
    CHECK (settled_amount_minor IS NULL OR settled_amount_minor >= 0)
);

CREATE TABLE IF NOT EXISTS payment_orders (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_order_no varchar(40) NOT NULL UNIQUE,
    legal_entity_id uuid NOT NULL REFERENCES legal_entities(id),
    customer_id uuid REFERENCES customers(id),
    source_account_id uuid REFERENCES accounts(id),
    destination_account_id uuid REFERENCES accounts(id),
    payment_method_id uuid REFERENCES payment_methods(id),
    counterparty_id uuid REFERENCES counterparties(id),
    settlement_batch_id uuid REFERENCES settlement_batches(id),
    order_type varchar(20) NOT NULL CHECK (order_type IN ('card_charge', 'bank_transfer', 'wallet_transfer', 'payout', 'refund', 'reversal', 'adjustment')),
    direction varchar(20) NOT NULL CHECK (direction IN ('inbound', 'outbound', 'internal')),
    status varchar(30) NOT NULL DEFAULT 'created' CHECK (status IN ('created', 'pending_authorization', 'authorized', 'captured', 'settled', 'failed', 'canceled', 'refunded', 'reversed')),
    amount_minor bigint NOT NULL CHECK (amount_minor > 0),
    fee_amount_minor bigint NOT NULL DEFAULT 0 CHECK (fee_amount_minor >= 0),
    currency_code varchar(3) NOT NULL REFERENCES currencies(code),
    fx_rate_id uuid REFERENCES fx_rates(id),
    idempotency_key text,
    external_reference text,
    description text,
    requested_at timestamptz NOT NULL DEFAULT now(),
    authorized_at timestamptz,
    captured_at timestamptz,
    completed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (source_account_id IS NOT NULL OR payment_method_id IS NOT NULL),
    CHECK (destination_account_id IS NOT NULL OR counterparty_id IS NOT NULL),
    CHECK (fee_amount_minor <= amount_minor)
);

CREATE TABLE IF NOT EXISTS payment_order_events (
    id bigserial PRIMARY KEY,
    payment_order_id uuid NOT NULL REFERENCES payment_orders(id) ON DELETE CASCADE,
    event_type varchar(30) NOT NULL CHECK (event_type IN ('created', 'authorization_requested', 'authorized', 'capture_requested', 'captured', 'settled', 'failed', 'canceled', 'refunded', 'reversed', 'note_added')),
    from_status varchar(30),
    to_status varchar(30),
    actor_type varchar(20) NOT NULL CHECK (actor_type IN ('system', 'customer', 'operator', 'webhook')),
    actor_reference text,
    event_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS authorization_holds (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_order_id uuid NOT NULL UNIQUE REFERENCES payment_orders(id) ON DELETE CASCADE,
    account_id uuid NOT NULL REFERENCES accounts(id),
    currency_code varchar(3) NOT NULL REFERENCES currencies(code),
    amount_minor bigint NOT NULL CHECK (amount_minor > 0),
    hold_status varchar(20) NOT NULL DEFAULT 'active' CHECK (hold_status IN ('active', 'released', 'captured', 'expired')),
    expires_at timestamptz NOT NULL,
    released_at timestamptz,
    captured_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (expires_at > created_at),
    CHECK (released_at IS NULL OR captured_at IS NULL)
);

CREATE TABLE IF NOT EXISTS journal_entries (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    entry_no varchar(40) NOT NULL UNIQUE,
    legal_entity_id uuid NOT NULL REFERENCES legal_entities(id),
    payment_order_id uuid REFERENCES payment_orders(id),
    entry_type varchar(20) NOT NULL CHECK (entry_type IN ('payment', 'fee', 'settlement', 'refund', 'adjustment', 'reversal')),
    status varchar(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'posted', 'reversed')),
    effective_at timestamptz NOT NULL,
    posted_at timestamptz,
    reversal_of_entry_id uuid REFERENCES journal_entries(id),
    description text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (status <> 'posted' OR posted_at IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS journal_entry_lines (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    journal_entry_id uuid NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
    line_no smallint NOT NULL CHECK (line_no > 0),
    account_id uuid NOT NULL REFERENCES accounts(id),
    entry_side varchar(10) NOT NULL CHECK (entry_side IN ('debit', 'credit')),
    amount_minor bigint NOT NULL CHECK (amount_minor > 0),
    currency_code varchar(3) NOT NULL REFERENCES currencies(code),
    memo text,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (journal_entry_id, line_no)
);

CREATE INDEX IF NOT EXISTS idx_customers_legal_entity_id ON customers (legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_customers_status ON customers (status);

CREATE INDEX IF NOT EXISTS idx_customer_addresses_customer_id ON customer_addresses (customer_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_customer_primary_address ON customer_addresses (customer_id, address_type) WHERE is_primary;

CREATE INDEX IF NOT EXISTS idx_customer_identities_customer_id ON customer_identities (customer_id);
CREATE INDEX IF NOT EXISTS idx_customer_identities_status ON customer_identities (status);

CREATE INDEX IF NOT EXISTS idx_counterparties_legal_entity_id ON counterparties (legal_entity_id);

CREATE INDEX IF NOT EXISTS idx_payment_methods_customer_id ON payment_methods (customer_id);
CREATE INDEX IF NOT EXISTS idx_payment_methods_status ON payment_methods (status);

CREATE INDEX IF NOT EXISTS idx_accounts_customer_id ON accounts (customer_id);
CREATE INDEX IF NOT EXISTS idx_accounts_parent_account_id ON accounts (parent_account_id);
CREATE INDEX IF NOT EXISTS idx_accounts_currency_code ON accounts (currency_code);

CREATE INDEX IF NOT EXISTS idx_fx_rates_pair_date ON fx_rates (from_currency_code, to_currency_code, rate_date DESC);

CREATE INDEX IF NOT EXISTS idx_settlement_batches_legal_entity_id ON settlement_batches (legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_settlement_batches_status ON settlement_batches (batch_status);

CREATE INDEX IF NOT EXISTS idx_payment_orders_customer_id ON payment_orders (customer_id);
CREATE INDEX IF NOT EXISTS idx_payment_orders_status_requested_at ON payment_orders (status, requested_at DESC);
CREATE INDEX IF NOT EXISTS idx_payment_orders_settlement_batch_id ON payment_orders (settlement_batch_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_payment_orders_idempotency ON payment_orders (legal_entity_id, idempotency_key) WHERE idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_payment_order_events_order_created_at ON payment_order_events (payment_order_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_authorization_holds_account_id ON authorization_holds (account_id);
CREATE INDEX IF NOT EXISTS idx_authorization_holds_status ON authorization_holds (hold_status);

CREATE INDEX IF NOT EXISTS idx_journal_entries_payment_order_id ON journal_entries (payment_order_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_journal_entries_reversal_of_entry_id ON journal_entries (reversal_of_entry_id) WHERE reversal_of_entry_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_journal_entry_lines_account_id ON journal_entry_lines (account_id);
CREATE INDEX IF NOT EXISTS idx_journal_entry_lines_currency_code ON journal_entry_lines (currency_code);

DROP TRIGGER IF EXISTS trg_legal_entities_set_updated_at ON legal_entities;
CREATE TRIGGER trg_legal_entities_set_updated_at
BEFORE UPDATE ON legal_entities
FOR EACH ROW
EXECUTE FUNCTION fintrain.set_updated_at();

DROP TRIGGER IF EXISTS trg_customers_set_updated_at ON customers;
CREATE TRIGGER trg_customers_set_updated_at
BEFORE UPDATE ON customers
FOR EACH ROW
EXECUTE FUNCTION fintrain.set_updated_at();

DROP TRIGGER IF EXISTS trg_counterparties_set_updated_at ON counterparties;
CREATE TRIGGER trg_counterparties_set_updated_at
BEFORE UPDATE ON counterparties
FOR EACH ROW
EXECUTE FUNCTION fintrain.set_updated_at();

DROP TRIGGER IF EXISTS trg_payment_methods_set_updated_at ON payment_methods;
CREATE TRIGGER trg_payment_methods_set_updated_at
BEFORE UPDATE ON payment_methods
FOR EACH ROW
EXECUTE FUNCTION fintrain.set_updated_at();

DROP TRIGGER IF EXISTS trg_accounts_set_updated_at ON accounts;
CREATE TRIGGER trg_accounts_set_updated_at
BEFORE UPDATE ON accounts
FOR EACH ROW
EXECUTE FUNCTION fintrain.set_updated_at();

DROP TRIGGER IF EXISTS trg_account_balances_set_updated_at ON account_balances;
CREATE TRIGGER trg_account_balances_set_updated_at
BEFORE UPDATE ON account_balances
FOR EACH ROW
EXECUTE FUNCTION fintrain.set_updated_at();

DROP TRIGGER IF EXISTS trg_settlement_batches_set_updated_at ON settlement_batches;
CREATE TRIGGER trg_settlement_batches_set_updated_at
BEFORE UPDATE ON settlement_batches
FOR EACH ROW
EXECUTE FUNCTION fintrain.set_updated_at();

DROP TRIGGER IF EXISTS trg_payment_orders_set_updated_at ON payment_orders;
CREATE TRIGGER trg_payment_orders_set_updated_at
BEFORE UPDATE ON payment_orders
FOR EACH ROW
EXECUTE FUNCTION fintrain.set_updated_at();

DROP TRIGGER IF EXISTS trg_authorization_holds_set_updated_at ON authorization_holds;
CREATE TRIGGER trg_authorization_holds_set_updated_at
BEFORE UPDATE ON authorization_holds
FOR EACH ROW
EXECUTE FUNCTION fintrain.set_updated_at();

DROP TRIGGER IF EXISTS trg_journal_entries_set_updated_at ON journal_entries;
CREATE TRIGGER trg_journal_entries_set_updated_at
BEFORE UPDATE ON journal_entries
FOR EACH ROW
EXECUTE FUNCTION fintrain.set_updated_at();

