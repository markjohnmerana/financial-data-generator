from fintrain_loader.core import LoadState, TableModule


class LegalEntitiesModule(TableModule):
    name = "legal_entities"
    columns = (
        "id",
        "entity_code",
        "legal_name",
        "display_name",
        "entity_type",
        "country_code",
        "base_currency_code",
        "status",
        "created_at",
        "updated_at",
    )

    def row_count(self, state: LoadState) -> int:
        return state.counts.legal_entities

    def iter_rows(self, state: LoadState):
        for index in range(state.counts.legal_entities):
            yield self.project(state.legal_entity_snapshot(index))
