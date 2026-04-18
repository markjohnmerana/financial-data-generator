from fintrain_loader.core import LoadState, TableModule


class AccountBalancesModule(TableModule):
    name = "account_balances"
    columns = (
        "account_id",
        "posted_balance_minor",
        "pending_inflow_minor",
        "pending_outflow_minor",
        "balance_version",
        "updated_at",
    )

    def row_count(self, state: LoadState) -> int:
        return state.total_accounts

    def iter_rows(self, state: LoadState):
        for index in range(state.total_accounts):
            yield self.project(state.account_balance_snapshot(index))
