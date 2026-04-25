from fintrain_loader.core import LoadState, TableModule


class FxRatesModule(TableModule):
    name = "fx_rates"
    columns = (
        "id",
        "rate_date",
        "from_currency_code",
        "to_currency_code",
        "provider_name",
        "rate",
        "captured_at",
        "created_at",
    )

    def row_count(self, state: LoadState) -> int:
        return state.total_fx_rates

    def iter_rows(self, state: LoadState):
        for index in range(state.total_fx_rates):
            yield self.project(state.fx_rate_snapshot(index))
