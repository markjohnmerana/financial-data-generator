from fintrain_loader.core import LoadState, TableModule


class PaymentOrdersModule(TableModule):
    name = "payment_orders"
    columns = (
        "id",
        "payment_order_no",
        "legal_entity_id",
        "customer_id",
        "source_account_id",
        "destination_account_id",
        "payment_method_id",
        "counterparty_id",
        "settlement_batch_id",
        "order_type",
        "direction",
        "status",
        "amount_minor",
        "fee_amount_minor",
        "currency_code",
        "fx_rate_id",
        "idempotency_key",
        "external_reference",
        "description",
        "requested_at",
        "authorized_at",
        "captured_at",
        "completed_at",
        "created_at",
        "updated_at",
    )

    def row_count(self, state: LoadState) -> int:
        return state.counts.payment_orders

    def iter_rows(self, state: LoadState):
        for index in range(state.counts.payment_orders):
            yield self.project(state.payment_order_snapshot(index))
