"""Data models for the apartment management system."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


class Parameters(BaseModel):
    """Configuration parameters for the apartment management system.

    Attributes:
        apartments_json_path: Path to apartments data file.
        tenants_json_path: Path to tenants data file.
        transfers_json_path: Path to transfers data file.
        bills_json_path: Path to bills data file.
        tenants_blacklist_json_path: Path to blacklist data file.
        apartment_events_json_path: Path to apartment events data file.
        max_transfer_pln: Maximum allowed transfer amount.
        max_refund_pln: Maximum allowed refund amount.

    Example:
        >>> parameters = Parameters()
        >>> parameters.max_transfer_pln
        4500.0

    """

    apartments_json_path: str = "data/apartments.json"
    tenants_json_path: str = "data/tenants.json"
    transfers_json_path: str = "data/transfers.json"
    bills_json_path: str = "data/bills.json"
    tenants_blacklist_json_path: str = "data/tenants_blacklist.json"
    apartment_events_json_path: str = "data/apartment_events.json"

    max_transfer_pln: float = Field(default=4500.0, ge=0)
    max_refund_pln: float = Field(default=2500.0, ge=0)


class Room(BaseModel):
    """A room model in the apartment.

    Attributes:
        name: Room name.
        area_m2: Room area in square meters.

    Example:
        >>> room = Room(name="Bedroom", area_m2=14.5)
        >>> room.name
        'Bedroom'

    """

    name: str
    area_m2: float = Field(..., gt=0)


class Apartment(BaseModel):
    """Apartment model containing apartment details and rooms.

    Attributes:
        key: Unique apartment identifier.
        name: Apartment name.
        location: Apartment location.
        area_m2: Total apartment area.
        rooms: Dictionary of apartment rooms.

    Example:
        >>> apartment = Apartment(
        ...     key="APT001",
        ...     name="Green Apartment",
        ...     location="Warsaw",
        ...     area_m2=65.0,
        ...     rooms={}
        ... )
        >>> apartment.location
        'Warsaw'

    """

    key: str
    name: str
    location: str
    area_m2: float = Field(..., gt=0)
    rooms: dict[str, Room]

    @staticmethod
    def from_json_file(file_path: str) -> dict[str, Apartment]:
        """Load apartments from a JSON file.

        Args:
            file_path: Path to JSON file.

        Returns:
            Dictionary mapping apartment keys to Apartment objects.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If JSON structure is invalid.

        Example:
            >>> apartments = Apartment.from_json_file(
            ...     "data/apartments.json"
            ... )
            >>> isinstance(apartments, dict)
            True

        """
        path = Path(file_path)

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Expected a dictionary of apartments.")

        return {key: Apartment(**apartment) for key, apartment in data.items()}


class Tenant(BaseModel):
    """Tenant model in the apartment management system.

    Attributes:
        name: Tenant full name.
        apartment: Apartment identifier.
        room: Assigned room.
        rent_pln: Monthly rent amount.
        deposit_pln: Deposit amount.
        date_agreement_from: Contract start date.
        date_agreement_to: Contract end date.

    Example:
        >>> tenant = Tenant(
        ...     name="John Smith",
        ...     apartment="APT001",
        ...     room="Room A",
        ...     rent_pln=2500,
        ...     deposit_pln=3000,
        ...     date_agreement_from="2024-01-01",
        ...     date_agreement_to="2024-12-31"
        ... )
        >>> tenant.rent_pln
        2500

    """

    name: str
    apartment: str
    room: str
    rent_pln: float = Field(..., ge=0)
    deposit_pln: float = Field(..., ge=0)
    date_agreement_from: str
    date_agreement_to: str

    @staticmethod
    def from_json_file(file_path: str) -> dict[str, Tenant]:
        """Load tenants from a JSON file.

        Args:
            file_path: Path to JSON file.

        Returns:
            Dictionary mapping tenant keys to Tenant objects.

        Raises:
            ValueError: If JSON structure is invalid.

        Example:
            >>> tenants = Tenant.from_json_file(
            ...     "data/tenants.json"
            ... )
            >>> isinstance(tenants, dict)
            True

        """
        path = Path(file_path)

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Expected a dictionary of tenants.")

        return {key: Tenant(**tenant) for key, tenant in data.items()}


class TenantBlacklistEntry(BaseModel):
    """Blacklist entry for a tenant.

    Attributes:
        tenant: Tenant name.
        reason: Blacklist reason.

    Example:
        >>> entry = TenantBlacklistEntry(
        ...     tenant="John Smith",
        ...     reason="Unpaid rent"
        ... )
        >>> entry.reason
        'Unpaid rent'

    """

    tenant: str
    reason: str

    @staticmethod
    def from_json_file(file_path: str) -> list[TenantBlacklistEntry]:
        """Load tenant blacklist entries from a JSON file.

        Args:
            file_path: Path to JSON file.

        Returns:
            List of blacklist entries.

        Example:
            >>> blacklist = (
            ...     TenantBlacklistEntry.from_json_file(
            ...         "data/tenants_blacklist.json"
            ...     )
            ... )
            >>> isinstance(blacklist, list)
            True

        """
        path = Path(file_path)

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError(
                "Expected a list of tenant blacklist entries.",
            )

        return [TenantBlacklistEntry(**entry) for entry in data]


class Transfer(BaseModel):
    """Financial transfer model.

    Attributes:
        amount_pln: Transfer amount.
        date: Transfer date.
        settlement_year: Settlement year.
        settlement_month: Settlement month.
        tenant: Tenant name.
        type: Transfer type.

    Example:
        >>> transfer = Transfer(
        ...     amount_pln=2500,
        ...     date="2024-03-01",
        ...     settlement_year=2024,
        ...     settlement_month=3,
        ...     tenant="John Smith"
        ... )
        >>> transfer.amount_pln
        2500

    """

    amount_pln: float = Field(..., ge=0)
    date: str
    settlement_year: int | None = None
    settlement_month: int | None = None
    tenant: str
    type: str | None = None

    @staticmethod
    def from_json_file(file_path: str) -> list[Transfer]:
        """Load transfers from a JSON file.

        Args:
            file_path: Path to JSON file.

        Returns:
            List of Transfer objects.

        Example:
            >>> transfers = Transfer.from_json_file(
            ...     "data/transfers.json"
            ... )
            >>> isinstance(transfers, list)
            True

        """
        path = Path(file_path)

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError("Expected a list of transfers.")

        return [Transfer(**transfer) for transfer in data]


class Bill(BaseModel):
    """Financial bill model.

    Attributes:
        amount_pln: Bill amount.
        date_due: Due date.
        apartment: Apartment identifier.
        settlement_year: Settlement year.
        settlement_month: Settlement month.
        type: Bill type.

    Example:
        >>> bill = Bill(
        ...     amount_pln=850,
        ...     date_due="2024-04-10",
        ...     apartment="APT001",
        ...     settlement_year=2024,
        ...     settlement_month=4,
        ...     type="Electricity"
        ... )
        >>> bill.type
        'Electricity'

    """

    amount_pln: float = Field(..., ge=0)
    date_due: str
    apartment: str
    settlement_year: int
    settlement_month: int
    type: str

    @staticmethod
    def from_json_file(file_path: str) -> list[Bill]:
        """Load bills from a JSON file.

        Args:
            file_path: Path to JSON file.

        Returns:
            List of Bill objects.

        Example:
            >>> bills = Bill.from_json_file("data/bills.json")
            >>> isinstance(bills, list)
            True

        """
        path = Path(file_path)

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError("Expected a list of bills.")

        return [Bill(**bill) for bill in data]


class ApartmentSettlement(BaseModel):
    """Financial summary for an apartment.

    Attributes:
        key: Settlement identifier.
        apartment: Apartment identifier.
        month: Settlement month.
        year: Settlement year.
        total_due_pln: Total amount due.
        total_transfers_pln: Total transfers amount.
        balance_pln: Final balance.

    Example:
        >>> settlement = ApartmentSettlement(
        ...     key="SET001",
        ...     apartment="APT001",
        ...     month=3,
        ...     year=2024,
        ...     total_due_pln=4000
        ... )
        >>> settlement.balance_pln
        0.0

    """

    key: str
    apartment: str
    month: int
    year: int
    total_due_pln: float = Field(..., ge=0)
    total_transfers_pln: float = Field(default=0.0, ge=0)
    balance_pln: float = 0.0


class TenantSettlement(BaseModel):
    """Financial summary for a tenant.

    Attributes:
        tenant: Tenant name.
        apartment_settlement: Related apartment settlement.
        month: Settlement month.
        year: Settlement year.
        total_due_pln: Total amount due.
        total_transfers_pln: Total transfers amount.
        balance_pln: Final balance.

    Example:
        >>> settlement = TenantSettlement(
        ...     tenant="John Smith",
        ...     apartment_settlement="SET001",
        ...     month=3,
        ...     year=2024,
        ...     total_due_pln=2500
        ... )
        >>> settlement.total_due_pln
        2500

    """

    tenant: str
    apartment_settlement: str
    month: int
    year: int
    total_due_pln: float = Field(..., ge=0)
    total_transfers_pln: float = Field(default=0.0, ge=0)
    balance_pln: float = 0.0


class ApartmentEvent(BaseModel):
    """Apartment event model.

    Attributes:
        date: Event date.
        apartment: Apartment identifier.
        amount_pln: Optional related amount.
        tenant: Related tenant.
        description: Event description.
        solved: Whether the issue is solved.

    Example:
        >>> event = ApartmentEvent(
        ...     date="2024-03-15",
        ...     apartment="APT001",
        ...     description="Broken washing machine"
        ... )
        >>> event.solved
        False

    """

    date: str
    apartment: str
    amount_pln: float | None = None
    tenant: str | None = None
    description: str
    solved: bool = False

    @staticmethod
    def from_json_file(file_path: str) -> list[ApartmentEvent]:
        """Load apartment events from a JSON file.

        Args:
            file_path: Path to JSON file.

        Returns:
            List of ApartmentEvent objects.

        Example:
            >>> events = ApartmentEvent.from_json_file(
            ...     "data/apartment_events.json"
            ... )
            >>> isinstance(events, list)
            True

        """
        path = Path(file_path)

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError(
                "Expected a list of apartment events.",
            )

        return [ApartmentEvent(**event) for event in data]
