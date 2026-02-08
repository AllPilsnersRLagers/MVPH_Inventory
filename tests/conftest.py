"""Shared test fixtures for inventory tests."""

from decimal import Decimal

import pytest

from inventory.models import Category, InventoryItem, Subcategory, UnitOfMeasure


@pytest.fixture
def hop_item(db: None) -> InventoryItem:
    """An ingredient item (hops) with stock above reorder point."""
    return InventoryItem.objects.create(
        name="Cascade Hops",
        category=Category.INGREDIENT,
        subcategory=Subcategory.HOPS,
        quantity_on_hand=Decimal("10.00"),
        unit_of_measure=UnitOfMeasure.OZ,
        reorder_point=Decimal("2.00"),
    )


@pytest.fixture
def low_stock_item(db: None) -> InventoryItem:
    """A chemical item at its reorder point (low stock)."""
    return InventoryItem.objects.create(
        name="PBW Cleaner",
        category=Category.CHEMICAL,
        subcategory=Subcategory.CLEANER,
        quantity_on_hand=Decimal("1.00"),
        unit_of_measure=UnitOfMeasure.LB,
        reorder_point=Decimal("2.00"),
    )


@pytest.fixture
def keg_item(db: None) -> InventoryItem:
    """A finished good item (keg)."""
    return InventoryItem.objects.create(
        name="Pale Ale Keg",
        category=Category.FINISHED_GOOD,
        subcategory=Subcategory.KEG,
        quantity_on_hand=Decimal("5.00"),
        unit_of_measure=UnitOfMeasure.EACH,
        reorder_point=Decimal("1.00"),
    )
