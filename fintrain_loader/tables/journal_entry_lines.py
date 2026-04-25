from fintrain_loader.core import LoadState, TableModule


class JournalEntryLinesModule(TableModule):
    name = "journal_entry_lines"
    columns = (
        "id",
        "journal_entry_id",
        "line_no",
        "account_id",
        "entry_side",
        "amount_minor",
        "currency_code",
        "memo",
        "created_at",
    )

    def iter_rows(self, state: LoadState):
        for index in range(state.counts.payment_orders):
            for row in state.journal_line_rows(index):
                yield self.project(row)
