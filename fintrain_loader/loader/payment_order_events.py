from fintrain_loader.core import LoadState, TableModule


class PaymentOrderEventsModule(TableModule):
    name = "payment_order_events"
    columns = (
        "payment_order_id",
        "event_type",
        "from_status",
        "to_status",
        "actor_type",
        "actor_reference",
        "event_payload",
        "created_at",
    )

    def iter_rows(self, state: LoadState):
        for index in range(state.counts.payment_orders):
            for row in state.payment_order_event_rows(index):
                yield self.project(row)
