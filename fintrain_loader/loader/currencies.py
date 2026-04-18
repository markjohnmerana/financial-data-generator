from fintrain_loader.core import LoadState, TableModule


class CurrenciesModule(TableModule):
    name = "currencies"
    columns = ("code", "numeric_code", "name", "minor_unit", "symbol", "is_active", "created_at")

    def row_count(self, state: LoadState) -> int:
        return len(state.currency_rows())

    def iter_rows(self, state: LoadState):
        for row in state.currency_rows():
            yield self.project(row)
