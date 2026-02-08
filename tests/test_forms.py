"""Tests for inventory forms."""

from decimal import Decimal

from inventory.forms import InventoryItemForm, StockAdjustmentForm
from inventory.models import Category, InventoryItem, Subcategory, UnitOfMeasure


class TestInventoryItemForm:
    """Tests for the InventoryItemForm."""

    def test_valid_form(self, db: None) -> None:
        data = {
            "name": "Cascade Hops",
            "category": Category.INGREDIENT,
            "subcategory": Subcategory.HOPS,
            "quantity_on_hand": "5.00",
            "unit_of_measure": UnitOfMeasure.OZ,
            "reorder_point": "2.00",
            "description": "",
            "notes": "",
        }
        form = InventoryItemForm(data=data)
        assert form.is_valid(), form.errors

    def test_missing_required_fields(self, db: None) -> None:
        form = InventoryItemForm(data={})
        assert not form.is_valid()
        assert "name" in form.errors
        assert "category" in form.errors

    def test_subcategory_choices_scoped_to_category(self, db: None) -> None:
        item = InventoryItem(category=Category.CHEMICAL)
        form = InventoryItemForm(instance=item)
        choice_values = [v for v, _ in form.fields["subcategory"].choices]  # type: ignore[attr-defined]
        assert "cleaner" in choice_values
        assert "hops" not in choice_values


class TestStockAdjustmentForm:
    """Tests for the StockAdjustmentForm."""

    def test_valid_positive_adjustment(self) -> None:
        form = StockAdjustmentForm(data={"adjustment": "5.00"})
        assert form.is_valid()

    def test_valid_negative_adjustment(self) -> None:
        form = StockAdjustmentForm(data={"adjustment": "-3.00"})
        assert form.is_valid()

    def test_apply_to_adds_stock(self, hop_item: InventoryItem) -> None:
        form = StockAdjustmentForm(data={"adjustment": "5.00"})
        form.is_valid()
        form.apply_to(hop_item)
        hop_item.refresh_from_db()
        assert hop_item.quantity_on_hand == Decimal("15.00")

    def test_apply_to_subtracts_stock(self, hop_item: InventoryItem) -> None:
        form = StockAdjustmentForm(data={"adjustment": "-3.00"})
        form.is_valid()
        form.apply_to(hop_item)
        hop_item.refresh_from_db()
        assert hop_item.quantity_on_hand == Decimal("7.00")

    def test_apply_to_floors_at_zero(self, hop_item: InventoryItem) -> None:
        form = StockAdjustmentForm(data={"adjustment": "-100.00"})
        form.is_valid()
        form.apply_to(hop_item)
        hop_item.refresh_from_db()
        assert hop_item.quantity_on_hand == Decimal("0.00")

    def test_missing_adjustment(self) -> None:
        form = StockAdjustmentForm(data={})
        assert not form.is_valid()
        assert "adjustment" in form.errors
