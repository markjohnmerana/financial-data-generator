

SET search_path TO fintrain, public;

INSERT INTO currencies (code, numeric_code, name, minor_unit, symbol)
VALUES
    ('PHP', '608', 'Philippine Peso', 2, 'PHP'),
    ('USD', '840', 'US Dollar', 2, 'USD'),
    ('EUR', '978', 'Euro', 2, 'EUR'),
    ('JPY', '392', 'Japanese Yen', 0, 'JPY')
ON CONFLICT (code) DO NOTHING;

INSERT INTO legal_entities (id, entity_code, legal_name, display_name, entity_type, country_code, base_currency_code, status)
VALUES
    ('11111111-1111-1111-1111-111111111111', 'LE-PH-001', 'Training Payments Platform Inc.', 'TPP Philippines', 'platform', 'PH', 'PHP', 'active')
ON CONFLICT (id) DO NOTHING;

INSERT INTO customers (id, customer_no, legal_entity_id, customer_type, status, email, phone, first_name, last_name, birth_date)
VALUES
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'CUST-000001', '11111111-1111-1111-1111-111111111111', 'individual', 'active', 'ana.reyes@example.com', '+639171234567', 'Ana', 'Reyes', '1994-03-18'),
    ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'CUST-000002', '11111111-1111-1111-1111-111111111111', 'individual', 'active', 'marco.santos@example.com', '+639189876543', 'Marco', 'Santos', '1991-09-02')
ON CONFLICT (id) DO NOTHING;

INSERT INTO customer_addresses (id, customer_id, address_type, line1, city, region, postal_code, country_code, is_primary)
VALUES
    ('a1a1a1a1-aaaa-4aaa-8aaa-aaaaaaaaaaa1', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'residential', '101 Sampaguita Street', 'Quezon City', 'Metro Manila', '1100', 'PH', true),
    ('b1b1b1b1-bbbb-4bbb-8bbb-bbbbbbbbbbb1', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'residential', '22 Mabini Avenue', 'Makati City', 'Metro Manila', '1200', 'PH', true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO customer_identities (id, customer_id, identity_type, issuing_country_code, id_number_hash, status, verified_at)
VALUES
    ('a2a2a2a2-aaaa-4aaa-8aaa-aaaaaaaaaaa2', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'passport', 'PH', '64c2ed3f2adf6b60db1f3e54fc0ea213f4427d2f6bb4976af6f401efc1d5a9aa', 'verified', '2026-04-10 09:15:00+08'),
    ('b2b2b2b2-bbbb-4bbb-8bbb-bbbbbbbbbbb2', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'drivers_license', 'PH', '935307b0d17de0f266f07e38a6a3ffd7808b3ce7e37f2f554e95d9222488aa2b', 'verified', '2026-04-10 09:20:00+08')
ON CONFLICT (id) DO NOTHING;

INSERT INTO counterparties (id, legal_entity_id, counterparty_code, counterparty_type, display_name, country_code, bank_name, bank_account_masked, external_reference, status)
VALUES
    ('cccccccc-cccc-cccc-cccc-cccccccccccc', '11111111-1111-1111-1111-111111111111', 'CP-BANK-001', 'bank', 'Metro National Bank', 'PH', 'Metro National Bank', '****9012', 'MBANK-9012', 'active'),
    ('dddddddd-dddd-dddd-dddd-dddddddddddd', '11111111-1111-1111-1111-111111111111', 'CP-MERCHANT-001', 'merchant', 'Acme Supplies', 'PH', NULL, NULL, 'MERCH-ACME-01', 'active')
ON CONFLICT (id) DO NOTHING;

INSERT INTO payment_methods (id, customer_id, method_type, provider_name, token_ref, masked_identifier, expiry_month, expiry_year, status, is_default)
VALUES
    ('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'card', 'Visa', 'tok_ana_visa_001', '411111******1111', 10, 2028, 'active', true),
    ('ffffffff-ffff-ffff-ffff-ffffffffffff', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'bank_account', 'Metro National Bank', 'tok_marco_bank_001', 'PH55********8899', NULL, NULL, 'active', true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO accounts (id, account_no, legal_entity_id, customer_id, parent_account_id, account_name, account_category, account_role, normal_balance, currency_code, status, allow_overdraft)
VALUES
    ('10000000-0000-0000-0000-000000000001', '100100', '11111111-1111-1111-1111-111111111111', NULL, NULL, 'Operating Bank - PHP', 'asset', 'operating_cash', 'debit', 'PHP', 'active', false),
    ('10000000-0000-0000-0000-000000000002', '100200', '11111111-1111-1111-1111-111111111111', NULL, NULL, 'Settlement Clearing - PHP', 'asset', 'settlement', 'debit', 'PHP', 'active', false),
    ('20000000-0000-0000-0000-000000000001', '200100', '11111111-1111-1111-1111-111111111111', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', NULL, 'Ana Reyes Wallet - PHP', 'liability', 'customer_wallet', 'credit', 'PHP', 'active', false),
    ('20000000-0000-0000-0000-000000000002', '200200', '11111111-1111-1111-1111-111111111111', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', NULL, 'Marco Santos Wallet - PHP', 'liability', 'customer_wallet', 'credit', 'PHP', 'active', false),
    ('40000000-0000-0000-0000-000000000001', '400100', '11111111-1111-1111-1111-111111111111', NULL, NULL, 'Transaction Fee Income - PHP', 'revenue', 'fees_income', 'credit', 'PHP', 'active', false)
ON CONFLICT (id) DO NOTHING;

INSERT INTO account_balances (account_id, posted_balance_minor, pending_inflow_minor, pending_outflow_minor, balance_version)
VALUES
    ('10000000-0000-0000-0000-000000000001', 330000, 0, 0, 1),
    ('10000000-0000-0000-0000-000000000002', 0, 0, 0, 1),
    ('20000000-0000-0000-0000-000000000001', -200000, 0, 0, 2),
    ('20000000-0000-0000-0000-000000000002', -125000, 0, 0, 1),
    ('40000000-0000-0000-0000-000000000001', -5000, 0, 0, 2)
ON CONFLICT (account_id) DO NOTHING;

INSERT INTO fx_rates (id, rate_date, from_currency_code, to_currency_code, provider_name, rate, captured_at)
VALUES
    ('30000000-0000-0000-0000-000000000001', '2026-04-17', 'USD', 'PHP', 'ECB Snapshot', 56.2500000000, '2026-04-17 08:00:00+08'),
    ('30000000-0000-0000-0000-000000000002', '2026-04-17', 'EUR', 'PHP', 'ECB Snapshot', 63.1000000000, '2026-04-17 08:00:00+08')
ON CONFLICT (id) DO NOTHING;

INSERT INTO settlement_batches (id, batch_no, legal_entity_id, currency_code, settlement_account_id, batch_status, window_start_at, window_end_at, expected_amount_minor, settled_amount_minor, external_reference)
VALUES
    ('50000000-0000-0000-0000-000000000001', 'SETTLE-20260417-01', '11111111-1111-1111-1111-111111111111', 'PHP', '10000000-0000-0000-0000-000000000001', 'settled', '2026-04-17 09:00:00+08', '2026-04-17 12:00:00+08', 48500, 48500, 'BANK-SETTLEMENT-174500')
ON CONFLICT (id) DO NOTHING;

INSERT INTO payment_orders (
    id,
    payment_order_no,
    legal_entity_id,
    customer_id,
    source_account_id,
    destination_account_id,
    payment_method_id,
    counterparty_id,
    settlement_batch_id,
    order_type,
    direction,
    status,
    amount_minor,
    fee_amount_minor,
    currency_code,
    idempotency_key,
    external_reference,
    description,
    requested_at,
    authorized_at,
    captured_at,
    completed_at
)
VALUES
    (
        '60000000-0000-0000-0000-000000000001',
        'PO-20260417-0001',
        '11111111-1111-1111-1111-111111111111',
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        '20000000-0000-0000-0000-000000000001',
        NULL,
        NULL,
        'cccccccc-cccc-cccc-cccc-cccccccccccc',
        '50000000-0000-0000-0000-000000000001',
        'payout',
        'outbound',
        'settled',
        50000,
        1500,
        'PHP',
        'payout-ana-20260417-001',
        'EXT-PAYOUT-7781',
        'Customer wallet payout to Metro National Bank',
        '2026-04-17 09:25:00+08',
        '2026-04-17 09:25:35+08',
        '2026-04-17 09:27:10+08',
        '2026-04-17 11:55:00+08'
    )
ON CONFLICT (id) DO NOTHING;

INSERT INTO payment_order_events (id, payment_order_id, event_type, from_status, to_status, actor_type, actor_reference, event_payload, created_at)
VALUES
    (900001, '60000000-0000-0000-0000-000000000001', 'created', NULL, 'created', 'customer', 'ana.reyes@example.com', '{"channel":"mobile_app"}', '2026-04-17 09:25:00+08'),
    (900002, '60000000-0000-0000-0000-000000000001', 'authorized', 'created', 'authorized', 'system', 'risk-engine', '{"risk_score":12}', '2026-04-17 09:25:35+08'),
    (900003, '60000000-0000-0000-0000-000000000001', 'captured', 'authorized', 'captured', 'system', 'payments-core', '{"captured_amount_minor":50000}', '2026-04-17 09:27:10+08'),
    (900004, '60000000-0000-0000-0000-000000000001', 'settled', 'captured', 'settled', 'webhook', 'bank-webhook', '{"settled_amount_minor":48500}', '2026-04-17 11:55:00+08')
ON CONFLICT (id) DO NOTHING;

INSERT INTO authorization_holds (id, payment_order_id, account_id, currency_code, amount_minor, hold_status, expires_at, released_at, captured_at, created_at, updated_at)
VALUES
    ('70000000-0000-0000-0000-000000000001', '60000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001', 'PHP', 50000, 'captured', '2026-04-18 09:25:00+08', NULL, '2026-04-17 09:27:10+08', '2026-04-17 09:25:05+08', '2026-04-17 09:27:10+08')
ON CONFLICT (id) DO NOTHING;

INSERT INTO journal_entries (id, entry_no, legal_entity_id, payment_order_id, entry_type, status, effective_at, posted_at, reversal_of_entry_id, description)
VALUES
    (
        '80000000-0000-0000-0000-000000000001',
        'JE-20260417-0001',
        '11111111-1111-1111-1111-111111111111',
        '60000000-0000-0000-0000-000000000001',
        'payment',
        'posted',
        '2026-04-17 09:27:10+08',
        '2026-04-17 09:27:15+08',
        NULL,
        'Payout from Ana wallet to Metro National Bank'
    )
ON CONFLICT (id) DO NOTHING;

INSERT INTO journal_entry_lines (id, journal_entry_id, line_no, account_id, entry_side, amount_minor, currency_code, memo)
VALUES
    ('81000000-0000-0000-0000-000000000001', '80000000-0000-0000-0000-000000000001', 1, '20000000-0000-0000-0000-000000000001', 'debit', 50000, 'PHP', 'Reduce customer wallet liability'),
    ('81000000-0000-0000-0000-000000000002', '80000000-0000-0000-0000-000000000001', 2, '10000000-0000-0000-0000-000000000001', 'credit', 48500, 'PHP', 'Send funds to external bank'),
    ('81000000-0000-0000-0000-000000000003', '80000000-0000-0000-0000-000000000001', 3, '40000000-0000-0000-0000-000000000001', 'credit', 1500, 'PHP', 'Recognize payout fee income')
ON CONFLICT (id) DO NOTHING;

