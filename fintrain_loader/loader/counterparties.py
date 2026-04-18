from fintrain_loader.core import LoadState, TableModule


class CounterpartiesModule(TableModule):
    name = "counterparties"
    columns = (
        "id",
        "legal_entity_id",
        "counterparty_code",
        "counterparty_type",
        "display_name",
        "country_code",
        "bank_name",
        "bank_account_masked",
        "external_reference",
        "status",
        "created_at",
        "updated_at",
    )

    def row_count(self, state: LoadState) -> int:
        return state.counts.counterparties

    def iter_rows(self, state: LoadState):
        for index in range(state.counts.counterparties):
            yield self.project(state.counterparty_snapshot(index))
