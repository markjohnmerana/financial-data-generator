from fintrain_loader.core import LoadState, TableModule


class CustomerAddressesModule(TableModule):
    name = "customer_addresses"
    columns = (
        "id",
        "customer_id",
        "address_type",
        "line1",
        "line2",
        "city",
        "region",
        "postal_code",
        "country_code",
        "is_primary",
        "created_at",
    )

    def row_count(self, state: LoadState) -> int:
        return state.counts.customers

    def iter_rows(self, state: LoadState):
        for index in range(state.counts.customers):
            yield self.project(state.customer_address_snapshot(index))
