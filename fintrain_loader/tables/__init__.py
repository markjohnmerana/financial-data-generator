from fintrain_loader.tables.account_balances import AccountBalancesModule
from fintrain_loader.tables.accounts import AccountsModule
from fintrain_loader.tables.authorization_holds import AuthorizationHoldsModule
from fintrain_loader.tables.counterparties import CounterpartiesModule
from fintrain_loader.tables.currencies import CurrenciesModule
from fintrain_loader.tables.customer_addresses import CustomerAddressesModule
from fintrain_loader.tables.customer_identities import CustomerIdentitiesModule
from fintrain_loader.tables.customers import CustomersModule
from fintrain_loader.tables.fx_rates import FxRatesModule
from fintrain_loader.tables.journal_entries import JournalEntriesModule
from fintrain_loader.tables.journal_entry_lines import JournalEntryLinesModule
from fintrain_loader.tables.legal_entities import LegalEntitiesModule
from fintrain_loader.tables.payment_methods import PaymentMethodsModule
from fintrain_loader.tables.payment_order_events import PaymentOrderEventsModule
from fintrain_loader.tables.payment_orders import PaymentOrdersModule
from fintrain_loader.tables.settlement_batches import SettlementBatchesModule


def build_modules():
    return [
        CurrenciesModule(),
        LegalEntitiesModule(),
        CustomersModule(),
        CustomerAddressesModule(),
        CustomerIdentitiesModule(),
        CounterpartiesModule(),
        PaymentMethodsModule(),
        AccountsModule(),
        FxRatesModule(),
        SettlementBatchesModule(),
        PaymentOrdersModule(),
        PaymentOrderEventsModule(),
        AuthorizationHoldsModule(),
        JournalEntriesModule(),
        JournalEntryLinesModule(),
        AccountBalancesModule(),
    ]
