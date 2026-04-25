from fintrain_loader.core import LoadState, TableModule


class CustomersModule(TableModule):
    name = "customers"
    columns = (
        "id",
        "customer_no",
        "legal_entity_id",
        "customer_type",
        "status",
        "email",
        "phone",
        "first_name",
        "last_name",
        "birth_date",
        "created_at",
        "updated_at",
    )

    def row_count(self, state: LoadState) -> int:
        return state.counts.customers

    def iter_rows(self, state: LoadState):
        for index in range(state.counts.customers):
            yield self.project(state.customer_snapshot(index))
