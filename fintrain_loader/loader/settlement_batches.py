from fintrain_loader.core import LoadState, TableModule


class SettlementBatchesModule(TableModule):
    name = "settlement_batches"
    columns = (
        "id",
        "batch_no",
        "legal_entity_id",
        "currency_code",
        "settlement_account_id",
        "batch_status",
        "window_start_at",
        "window_end_at",
        "expected_amount_minor",
        "settled_amount_minor",
        "external_reference",
        "created_at",
        "updated_at",
    )

    def row_count(self, state: LoadState) -> int:
        return state.counts.settlement_batches

    def iter_rows(self, state: LoadState):
        for index in range(state.counts.settlement_batches):
            yield self.project(state.settlement_batch_snapshot(index))
