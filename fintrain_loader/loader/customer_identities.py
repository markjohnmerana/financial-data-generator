from fintrain_loader.core import LoadState, TableModule


class CustomerIdentitiesModule(TableModule):
    name = "customer_identities"
    columns = (
        "id",
        "customer_id",
        "identity_type",
        "issuing_country_code",
        "id_number_hash",
        "status",
        "verified_at",
        "created_at",
    )

    def row_count(self, state: LoadState) -> int:
        return state.counts.customers

    def iter_rows(self, state: LoadState):
        for index in range(state.counts.customers):
            yield self.project(state.customer_identity_snapshot(index))
