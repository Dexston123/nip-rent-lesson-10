"""Manager class for handling apartment management operations."""

from datetime import datetime

from src.models import (
    Apartment,
    ApartmentEvent,
    ApartmentSettlement,
    Bill,
    Parameters,
    Tenant,
    TenantBlacklistEntry,
    TenantSettlement,
    Transfer,
)


class Manager:
    """Manager class responsible for loading data and providing methods
    to manage apartments, tenants, transfers, bills, and apartment events.

    Attributes:
        parameters (Parameters): Configuration object containing file paths and constraints.
        apartments (Dict[str, Apartment]): Dictionary of apartment objects indexed by their keys.
        tenants (Dict[str, Tenant]): Dictionary of tenant objects indexed by their identifiers.
        transfers (List[Transfer]): List of all financial transfers recorded.
        bills (List[Bill]): List of all bills associated with apartments.
        tenants_blacklist (List[TenantBlacklistEntry]): List of blacklisted tenants.
        apartment_events (List[ApartmentEvent]): List of events (e.g., repairs) reported for apartments.

    """

    def __init__(self, parameters: Parameters):
        """Initializes the Manager with provided parameters and loads data from files.

        Args:
            parameters (Parameters): An instance of Parameters class containing settings.

        """
        self.parameters = parameters

        self.apartments: dict[str, Apartment] = {}
        self.tenants: dict[str, Tenant] = {}
        self.transfers: list[Transfer] = []
        self.bills: list[Bill] = []
        self.tenants_blacklist: list[TenantBlacklistEntry] = []
        self.apartment_events: list[ApartmentEvent] = []

        self.load_data()

    def load_data(self):
        """Load data from JSON files specified in the parameters.

        Populates apartments, tenants, transfers, bills, and blacklist from storage.
        """
        self.apartments = Apartment.from_json_file(self.parameters.apartments_json_path)
        self.tenants = Tenant.from_json_file(self.parameters.tenants_json_path)
        self.transfers = Transfer.from_json_file(self.parameters.transfers_json_path)
        self.bills = Bill.from_json_file(self.parameters.bills_json_path)
        self.tenants_blacklist = TenantBlacklistEntry.from_json_file(
            self.parameters.tenants_blacklist_json_path,
        )

    def load_additional_data(self):
        """Load additional data such as apartment events from JSON files."""
        self.apartment_events = ApartmentEvent.from_json_file(
            self.parameters.apartment_events_json_path,
        )

    def generate_apartment_events_report(
        self,
        apartment_key: str,
        only_unsolved: bool = True,
    ) -> list[ApartmentEvent]:
        """Generate a report of apartment events for a given apartment key.

        Args:
            apartment_key (str): Unique identifier of the apartment.
            only_unsolved (bool): If True, only returns events that are not yet solved.
                Defaults to True.

        Returns:
            List[ApartmentEvent]: A filtered list of apartment events.

        Raises:
            ValueError: If the provided apartment_key does not exist in the database.

        """
        if apartment_key not in self.apartments:
            raise ValueError("Apartment key does not exist")
        return [
            event
            for event in self.apartment_events
            if event.apartment == apartment_key
            and (not event.solved or not only_unsolved)
        ]

    def check_tenants_apartment_keys(self) -> bool:
        """Check if all tenants have valid apartment keys.

        Returns:
            bool: True if all tenants are assigned to existing apartments, False otherwise.

        """
        for tenant in self.tenants.values():
            if tenant.apartment not in self.apartments:
                return False
        return True

    def get_apartment(self, apartment_key: str) -> Apartment | None:
        """Get an apartment by its key.

        Args:
            apartment_key (str): Unique identifier of the apartment.

        Returns:
            Optional[Apartment]: Apartment object if found, None otherwise.

        """
        return self.apartments.get(apartment_key, None)

    def get_apartment_costs(
        self,
        apartment_key: str,
        year: int | None = None,
        month: int | None = None,
    ) -> float | None:
        """Calculate the total costs for a given apartment, optionally filtered by time.

        Args:
            apartment_key (str): Unique identifier of the apartment.
            year (int, optional): The year to filter costs.
            month (int, optional): The month to filter costs (1-12).

        Returns:
            Optional[float]: Total cost in PLN, or None if apartment not found.

        Raises:
            ValueError: If the month is provided but outside the 1-12 range.

        """
        if month is not None and (month < 1 or month > 12):
            raise ValueError("Month must be between 1 and 12")
        if apartment_key not in self.apartments:
            return None
        total_cost = 0.0
        for bill in self.bills:
            if (
                bill.apartment == apartment_key
                and (year is None or bill.settlement_year == year)
                and (month is None or bill.settlement_month == month)
            ):
                total_cost += bill.amount_pln
        return total_cost

    def get_settlement(
        self,
        apartment_key: str,
        year: int,
        month: int,
    ) -> ApartmentSettlement | None:
        """Get the apartment settlement for a specific period.

        Args:
            apartment_key (str): Unique identifier of the apartment.
            year (int): Settlement year.
            month (int): Settlement month (1-12).

        Returns:
            Optional[ApartmentSettlement]: Settlement object containing total due,
                or None if no data found.

        Raises:
            ValueError: If the month is outside the 1-12 range.

        """
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12")
        if apartment_key not in self.apartments:
            return None
        total_cost = self.get_apartment_costs(apartment_key, year, month)
        if total_cost is None:
            return None

        return ApartmentSettlement(
            key=f"{apartment_key}-{year}-{month}",
            apartment=apartment_key,
            year=year,
            month=month,
            total_due_pln=total_cost,
        )

    def create_tenants_settlements(
        self,
        apartment_settlement: ApartmentSettlement,
    ) -> list[TenantSettlement] | None:
        """Divide the apartment settlement costs among all tenants in that apartment.

        Args:
            apartment_settlement (ApartmentSettlement): The total settlement for the apartment.

        Returns:
            Optional[List[TenantSettlement]]: A list of individual settlements per tenant.
                Returns an empty list if no tenants are found.

        Raises:
            ValueError: If the settlement month is invalid.

        """
        if apartment_settlement.month < 1 or apartment_settlement.month > 12:
            raise ValueError("Month must be between 1 and 12")
        if apartment_settlement.apartment not in self.apartments:
            return None
        tenants_in_apartment = [
            tenant
            for tenant in self.tenants.values()
            if tenant.apartment == apartment_settlement.apartment
        ]
        if not tenants_in_apartment:
            return []

        return [
            TenantSettlement(
                tenant=tenant.name,
                apartment_settlement=apartment_settlement.key,
                month=apartment_settlement.month,
                year=apartment_settlement.year,
                total_due_pln=apartment_settlement.total_due_pln
                / len(tenants_in_apartment),
            )
            for tenant in tenants_in_apartment
        ]

    def get_debtors(self, apartment_key: str, year: int, month: int) -> list[str]:
        """Identify tenants who have not fully paid their dues for a given period.

        Args:
            apartment_key (str): Unique identifier of the apartment.
            year (int): Year to check.
            month (int): Month to check.

        Returns:
            List[str]: A list of names of tenants with outstanding debt.

        """
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12")
        output = []
        settlement = self.get_settlement(apartment_key, year, month)
        tenant_settlements = self.create_tenants_settlements(settlement)

        for tenant_settlement in tenant_settlements:
            tenant_transfers = [
                transfer
                for transfer in self.transfers
                if self.tenants[transfer.tenant].name == tenant_settlement.tenant
                and transfer.settlement_year == year
                and transfer.settlement_month == month
            ]
            total_paid = sum(
                transfer.amount_pln
                for transfer in tenant_transfers
                if transfer.settlement_year == year
                and transfer.settlement_month == month
            )
            if total_paid < tenant_settlement.total_due_pln:
                output.append(tenant_settlement.tenant)
        return output

    def calculate_tax(self, year: int, month: int, tax_rate: float) -> float:
        """Calculate the tax amount based on the total income from transfers.

        Args:
            year (int): Tax year.
            month (int): Tax month.
            tax_rate (float): Tax rate as a decimal (e.g., 0.085 for 8.5%).

        Returns:
            float: Rounded tax amount to the nearest integer.

        """
        total_income = sum(
            transfer.amount_pln
            for transfer in self.transfers
            if transfer.settlement_year == year and transfer.settlement_month == month
        )
        return round(total_income * tax_rate, 0)

    def check_deposits(self) -> float:
        """Verify if the actual paid deposits match the required deposit amounts.

        Returns:
            float: The difference between total paid deposits and required deposits.
                Negative value indicates a deficit.

        """
        total_deposits = 0.0
        total_due = 0.0
        for _, tenant in self.tenants.items():
            total_deposits += sum(
                transfer.amount_pln
                for transfer in self.transfers
                if self.tenants[transfer.tenant].name == tenant.name
                and transfer.type == "deposit"
            )
            total_due += tenant.deposit_pln

        return total_deposits - total_due

    def get_annual_balance(self, year: int) -> float:
        """Calculate the annual financial balance (Income - Costs).

        Args:
            year (int): The year for which to calculate the balance.

        Returns:
            float: The net annual balance in PLN.

        """
        total_income = sum(
            transfer.amount_pln
            for transfer in self.transfers
            if transfer.settlement_year == year
        )
        total_due = sum(
            bill.amount_pln for bill in self.bills if bill.settlement_year == year
        )
        return total_income - total_due

    def has_any_bills(self, apartment_key: str, year: int, month: int) -> bool:
        """Check if there are any recorded bills for a specific apartment and period.

        Args:
            apartment_key (str): Unique identifier of the apartment.
            year (int): Year to check.
            month (int): Month to check.

        Returns:
            bool: True if at least one bill exists, False otherwise.

        Raises:
            ValueError: If month is invalid or apartment_key does not exist.

        """
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12")
        if apartment_key not in self.apartments:
            raise ValueError("Apartment key does not exist")
        return any(
            bill
            for bill in self.bills
            if bill.apartment == apartment_key
            and bill.settlement_year == year
            and bill.settlement_month == month
        )

    def check_transfers_amount_range(self) -> bool:
        """Validate if all transfer amounts are within allowed ranges.

        Returns:
            bool: True if all transfers are within parameters limits, False otherwise.

        """
        for transfer in self.transfers:
            if (
                transfer.amount_pln > self.parameters.max_transfer_pln
                or transfer.amount_pln < -self.parameters.max_refund_pln
            ):
                return False
        return True

    def check_tenant_blacklist(self, tenant_name: str) -> bool:
        """Check if a specific tenant is blacklisted.

        Args:
            tenant_name (str): Full name of the tenant.

        Returns:
            bool: True if the tenant is found in the blacklist.

        """
        return any(
            entry for entry in self.tenants_blacklist if entry.tenant == tenant_name
        )

    def check_transfers_tenant(self) -> bool:
        """Validate transfers against tenant data and agreement duration.

        Checks if the tenant exists and if the transfer settlement period
        falls within the agreement start and end dates.

        Returns:
            bool: True if all transfers are valid, False otherwise.

        """
        for transfer in self.transfers:
            if transfer.tenant not in self.tenants:
                return False
            if (
                transfer.settlement_year is not None
                and transfer.settlement_month is not None
            ):
                agreement_from = self.tenants[transfer.tenant].date_agreement_from
                agreement_from = datetime.strptime(agreement_from, "%Y-%m-%d").date()
                agreement_to = self.tenants[transfer.tenant].date_agreement_to
                agreement_to = datetime.strptime(agreement_to, "%Y-%m-%d").date()
                if (transfer.settlement_year < agreement_from.year) or (
                    transfer.settlement_year > agreement_to.year
                ):
                    return False

        return True
