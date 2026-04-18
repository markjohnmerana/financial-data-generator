from fintrain_loader.core import LoadState, TableModule


class JournalEntriesModule(TableModule):
    name = "journal_entries"
    columns = (
        "id",
        "entry_no",
        "legal_entity_id",
        "payment_order_id",
        "entry_type",
        "status",
        "effective_at",
        "posted_at",
        "reversal_of_entry_id",
        "description",
        "created_at",
        "updated_at",
    )

    def iter_rows(self, state: LoadState):
        for index in range(state.counts.payment_orders):
            row = state.journal_entry_snapshot(index)
            if row is not None:
                yield self.project(row)
