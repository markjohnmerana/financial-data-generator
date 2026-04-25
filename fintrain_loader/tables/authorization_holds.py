from fintrain_loader.core import LoadState, TableModule


class AuthorizationHoldsModule(TableModule):
    name = "authorization_holds"
    columns = (
        "id",
        "payment_order_id",
        "account_id",
        "currency_code",
        "amount_minor",
        "hold_status",
        "expires_at",
        "released_at",
        "captured_at",
        "created_at",
        "updated_at",
    )

    def iter_rows(self, state: LoadState):
        for index in range(state.counts.payment_orders):
            row = state.authorization_hold_snapshot(index)
            if row is not None:
                yield self.project(row)
