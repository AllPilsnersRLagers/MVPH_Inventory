"""Tests for inventory forms."""

from decimal import Decimal

from inventory.forms import (
    InventoryItemForm,
    QuickRecipeForm,
    RecipeForm,
    StockAdjustmentForm,
)
from inventory.models import (
    Category,
    InventoryItem,
    Recipe,
    Subcategory,
    UnitOfMeasure,
)


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

    def test_earmarked_for_field_exists(self, db: None) -> None:
        form = InventoryItemForm()
        assert "earmarked_for" in form.fields

    def test_earmarked_for_accepts_recipe(
        self, db: None, pale_ale_recipe: Recipe
    ) -> None:
        data = {
            "name": "Cascade Hops",
            "category": Category.INGREDIENT,
            "subcategory": Subcategory.HOPS,
            "quantity_on_hand": "5.00",
            "unit_of_measure": UnitOfMeasure.OZ,
            "reorder_point": "2.00",
            "description": "",
            "notes": "",
            "earmarked_for": [str(pale_ale_recipe.pk)],
        }
        form = InventoryItemForm(data=data)
        assert form.is_valid(), form.errors
        item = form.save()
        assert pale_ale_recipe in item.earmarked_for.all()

    def test_earmarked_for_accepts_multiple(self, db: None) -> None:
        recipe1 = Recipe.objects.create(name="Test IPA")
        recipe2 = Recipe.objects.create(name="Test Stout")
        data = {
            "name": "Cascade Hops",
            "category": Category.INGREDIENT,
            "subcategory": Subcategory.HOPS,
            "quantity_on_hand": "5.00",
            "unit_of_measure": UnitOfMeasure.OZ,
            "reorder_point": "2.00",
            "description": "",
            "notes": "",
            "earmarked_for": [str(recipe1.pk), str(recipe2.pk)],
        }
        form = InventoryItemForm(data=data)
        assert form.is_valid(), form.errors
        item = form.save()
        assert item.earmarked_for.count() == 2

    def test_earmarked_for_accepts_empty(self, db: None) -> None:
        data = {
            "name": "Cascade Hops",
            "category": Category.INGREDIENT,
            "subcategory": Subcategory.HOPS,
            "quantity_on_hand": "5.00",
            "unit_of_measure": UnitOfMeasure.OZ,
            "reorder_point": "2.00",
            "description": "",
            "notes": "",
            "earmarked_for": [],
        }
        form = InventoryItemForm(data=data)
        assert form.is_valid(), form.errors
        item = form.save()
        assert item.earmarked_for.count() == 0


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


class TestRecipeForm:
    """Tests for the RecipeForm."""

    def test_valid_form(self, db: None) -> None:
        form = RecipeForm(data={"name": "New IPA"})
        assert form.is_valid(), form.errors

    def test_missing_name(self, db: None) -> None:
        form = RecipeForm(data={"name": ""})
        assert not form.is_valid()
        assert "name" in form.errors

    def test_creates_recipe(self, db: None) -> None:
        form = RecipeForm(data={"name": "New IPA"})
        form.is_valid()
        recipe = form.save()
        assert Recipe.objects.filter(pk=recipe.pk).exists()


class TestQuickRecipeForm:
    """Tests for the QuickRecipeForm."""

    def test_valid_form(self, db: None) -> None:
        form = QuickRecipeForm(data={"name": "Quick Stout"})
        assert form.is_valid(), form.errors

    def test_creates_recipe(self, db: None) -> None:
        form = QuickRecipeForm(data={"name": "Quick Stout"})
        form.is_valid()
        recipe = form.save()
        assert Recipe.objects.filter(name="Quick Stout").exists()
        assert recipe.name == "Quick Stout"
