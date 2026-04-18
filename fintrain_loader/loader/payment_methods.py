from fintrain_loader.core import LoadState, TableModule


class PaymentMethodsModule(TableModule):
    name = "payment_methods"
    columns = (
        "id",
        "customer_id",
        "method_type",
        "provider_name",
        "token_ref",
        "masked_identifier",
        "expiry_month",
        "expiry_year",
        "status",
        "is_default",
        "created_at",
        "updated_at",
    )

    def row_count(self, state: LoadState) -> int:
        return state.counts.customers

    def iter_rows(self, state: LoadState):
        for index in range(state.counts.customers):
            yield self.project(state.payment_method_snapshot(index))
