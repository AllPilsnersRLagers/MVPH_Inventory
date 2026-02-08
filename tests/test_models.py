"""Tests for inventory models."""

from decimal import Decimal

from inventory.models import (
    SUBCATEGORY_MAP,
    Category,
    InventoryItem,
    Subcategory,
    UnitOfMeasure,
)


class TestInventoryItem:
    """Tests for the InventoryItem model."""

    def test_str(self, hop_item: InventoryItem) -> None:
        assert str(hop_item) == "Cascade Hops"

    def test_is_low_stock_false(self, hop_item: InventoryItem) -> None:
        assert hop_item.is_low_stock is False

    def test_is_low_stock_true_below(self, low_stock_item: InventoryItem) -> None:
        assert low_stock_item.is_low_stock is True

    def test_is_low_stock_true_at_reorder(self, db: None) -> None:
        item = InventoryItem.objects.create(
            name="Star San",
            category=Category.CHEMICAL,
            subcategory=Subcategory.SANITIZER,
            quantity_on_hand=Decimal("3.00"),
            unit_of_measure=UnitOfMeasure.OZ,
            reorder_point=Decimal("3.00"),
        )
        assert item.is_low_stock is True

    def test_subcategory_display(self, hop_item: InventoryItem) -> None:
        assert hop_item.subcategory_display == "Hops"

    def test_ordering(self, hop_item: InventoryItem, keg_item: InventoryItem) -> None:
        items = list(InventoryItem.objects.values_list("name", flat=True))
        assert items == ["Cascade Hops", "Pale Ale Keg"]

    def test_default_quantity(self, db: None) -> None:
        item = InventoryItem.objects.create(
            name="Test",
            category=Category.INGREDIENT,
            subcategory=Subcategory.MALT,
            unit_of_measure=UnitOfMeasure.LB,
        )
        assert item.quantity_on_hand == Decimal("0.00")
        assert item.reorder_point == Decimal("0.00")

    def test_timestamps_set(self, hop_item: InventoryItem) -> None:
        assert hop_item.created_at is not None
        assert hop_item.updated_at is not None


class TestSubcategoryMap:
    """Tests for the SUBCATEGORY_MAP constant."""

    def test_all_categories_have_subcategories(self) -> None:
        for category in Category:
            assert category.value in SUBCATEGORY_MAP

    def test_ingredient_subcategories(self) -> None:
        values = [v for v, _ in SUBCATEGORY_MAP[Category.INGREDIENT]]
        assert set(values) == {"malt", "hops", "yeast", "adjunct"}

    def test_chemical_subcategories(self) -> None:
        values = [v for v, _ in SUBCATEGORY_MAP[Category.CHEMICAL]]
        assert set(values) == {"cleaner", "sanitizer", "water_treatment"}

    def test_finished_good_subcategories(self) -> None:
        values = [v for v, _ in SUBCATEGORY_MAP[Category.FINISHED_GOOD]]
        assert set(values) == {"keg", "can", "bottle", "case"}
