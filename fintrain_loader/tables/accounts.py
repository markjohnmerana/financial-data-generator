from fintrain_loader.core import LoadState, TableModule


class AccountsModule(TableModule):
    name = "accounts"
    columns = (
        "id",
        "account_no",
        "legal_entity_id",
        "customer_id",
        "parent_account_id",
        "account_name",
        "account_category",
        "account_role",
        "normal_balance",
        "currency_code",
        "status",
        "allow_overdraft",
        "created_at",
        "updated_at",
    )

    def row_count(self, state: LoadState) -> int:
        return state.total_accounts

    def iter_rows(self, state: LoadState):
        for index in range(state.total_accounts):
            yield self.project(state.account_snapshot(index))
