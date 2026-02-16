"""Tests for inventory views."""

from decimal import Decimal

from django.test import Client

from inventory.models import (
    ActionType,
    Category,
    InventoryItem,
    ItemChangeLog,
    Recipe,
    Subcategory,
    UnitOfMeasure,
)


class TestAuthenticationRequired:
    """Tests that views require authentication."""

    def test_item_list_redirects_anonymous(self, db: None) -> None:
        client = Client()
        resp = client.get("/")
        assert resp.status_code == 302
        assert "/login/" in resp.url  # type: ignore[attr-defined]


class TestItemListView:
    """Tests for the item_list view."""

    def test_empty_list(self, authenticated_client: Client, db: None) -> None:
        resp = authenticated_client.get("/")
        assert resp.status_code == 200
        assert b"No items found" in resp.content

    def test_shows_items(
        self, authenticated_client: Client, hop_item: InventoryItem
    ) -> None:
        resp = authenticated_client.get("/")
        assert resp.status_code == 200
        assert b"Cascade Hops" in resp.content

    def test_filter_by_category(
        self,
        authenticated_client: Client,
        hop_item: InventoryItem,
        keg_item: InventoryItem,
    ) -> None:
        resp = authenticated_client.get("/?category=ingredient")
        assert b"Cascade Hops" in resp.content
        assert b"Pale Ale Keg" not in resp.content

    def test_search(
        self,
        authenticated_client: Client,
        hop_item: InventoryItem,
        keg_item: InventoryItem,
    ) -> None:
        resp = authenticated_client.get("/?search=cascade")
        assert b"Cascade Hops" in resp.content
        assert b"Pale Ale Keg" not in resp.content

    def test_filter_by_subcategory(
        self,
        authenticated_client: Client,
        hop_item: InventoryItem,
        db: None,
    ) -> None:
        InventoryItem.objects.create(
            name="2-Row Malt",
            category=Category.INGREDIENT,
            subcategory=Subcategory.MALT,
            quantity_on_hand=Decimal("50.00"),
            unit_of_measure=UnitOfMeasure.LB,
            reorder_point=Decimal("10.00"),
        )
        resp = authenticated_client.get("/?category=ingredient&subcategory=hops")
        assert b"Cascade Hops" in resp.content
        assert b"2-Row Malt" not in resp.content

    def test_sub_tabs_present_for_ingredients(
        self, authenticated_client: Client, hop_item: InventoryItem
    ) -> None:
        resp = authenticated_client.get("/?category=ingredient")
        assert resp.context["sub_tabs"]
        labels = [t["label"] for t in resp.context["sub_tabs"]]
        assert "All" in labels
        assert "Hops" in labels
        assert "Fruit/Flavor" in labels

    def test_sub_tabs_empty_for_chemicals(
        self, authenticated_client: Client, low_stock_item: InventoryItem
    ) -> None:
        resp = authenticated_client.get("/?category=chemical")
        assert resp.context["sub_tabs"] == []

    def test_sub_tabs_empty_for_all(
        self, authenticated_client: Client, hop_item: InventoryItem
    ) -> None:
        resp = authenticated_client.get("/")
        assert resp.context["sub_tabs"] == []

    def test_htmx_returns_partial(
        self, authenticated_client: Client, hop_item: InventoryItem
    ) -> None:
        resp = authenticated_client.get("/", HTTP_HX_REQUEST="true")
        assert resp.status_code == 200
        # Partial should NOT include the full base template <html> tag
        assert b"<html" not in resp.content
        assert b"Cascade Hops" in resp.content


class TestItemCreateView:
    """Tests for the item_create view."""

    def test_get_form(self, authenticated_client: Client, db: None) -> None:
        resp = authenticated_client.get("/items/create/")
        assert resp.status_code == 200
        assert b"New Item" in resp.content

    def test_post_creates_item(self, authenticated_client: Client, db: None) -> None:
        data = {
            "name": "2-Row Pale Malt",
            "category": Category.INGREDIENT,
            "subcategory": Subcategory.MALT,
            "quantity_on_hand": "50.00",
            "unit_of_measure": UnitOfMeasure.LB,
            "reorder_point": "10.00",
            "description": "",
            "notes": "",
            "earmarked_for": [],
        }
        resp = authenticated_client.post("/items/create/", data)
        assert resp.status_code == 302
        assert InventoryItem.objects.filter(name="2-Row Pale Malt").exists()

    def test_post_invalid_data(self, authenticated_client: Client, db: None) -> None:
        resp = authenticated_client.post("/items/create/", {"name": ""})
        assert resp.status_code == 200  # Re-renders form with errors


class TestItemDetailView:
    """Tests for the item_detail view."""

    def test_detail_page(
        self, authenticated_client: Client, hop_item: InventoryItem
    ) -> None:
        resp = authenticated_client.get(f"/items/{hop_item.pk}/")
        assert resp.status_code == 200
        assert b"Cascade Hops" in resp.content

    def test_404_for_missing(self, authenticated_client: Client, db: None) -> None:
        resp = authenticated_client.get("/items/00000000-0000-0000-0000-000000000000/")
        assert resp.status_code == 404


class TestItemUpdateView:
    """Tests for the item_update view."""

    def test_get_edit_form(
        self, authenticated_client: Client, hop_item: InventoryItem
    ) -> None:
        resp = authenticated_client.get(f"/items/{hop_item.pk}/edit/")
        assert resp.status_code == 200
        assert b"Cascade Hops" in resp.content

    def test_post_updates_item(
        self, authenticated_client: Client, hop_item: InventoryItem
    ) -> None:
        data = {
            "name": "Centennial Hops",
            "category": Category.INGREDIENT,
            "subcategory": Subcategory.HOPS,
            "quantity_on_hand": "10.00",
            "unit_of_measure": UnitOfMeasure.OZ,
            "reorder_point": "2.00",
            "description": "",
            "notes": "",
            "earmarked_for": [],
        }
        resp = authenticated_client.post(f"/items/{hop_item.pk}/edit/", data)
        assert resp.status_code == 302
        hop_item.refresh_from_db()
        assert hop_item.name == "Centennial Hops"


class TestItemDeleteView:
    """Tests for the item_delete view."""

    def test_get_confirmation(
        self, authenticated_client: Client, hop_item: InventoryItem
    ) -> None:
        resp = authenticated_client.get(f"/items/{hop_item.pk}/delete/")
        assert resp.status_code == 200
        assert b"Delete" in resp.content

    def test_post_deletes_item(
        self, authenticated_client: Client, hop_item: InventoryItem
    ) -> None:
        resp = authenticated_client.post(f"/items/{hop_item.pk}/delete/")
        assert resp.status_code == 302
        assert not InventoryItem.objects.filter(pk=hop_item.pk).exists()


class TestAdjustStockView:
    """Tests for the adjust_stock HTMX endpoint."""

    def test_get_returns_form(
        self, authenticated_client: Client, hop_item: InventoryItem
    ) -> None:
        resp = authenticated_client.get(f"/items/{hop_item.pk}/adjust-stock/")
        assert resp.status_code == 200
        assert b"adjustment" in resp.content

    def test_post_adjusts_stock(
        self, authenticated_client: Client, hop_item: InventoryItem
    ) -> None:
        resp = authenticated_client.post(
            f"/items/{hop_item.pk}/adjust-stock/", {"adjustment": "5.00"}
        )
        assert resp.status_code == 200
        hop_item.refresh_from_db()
        assert hop_item.quantity_on_hand == Decimal("15.00")


class TestSubcategoryOptionsView:
    """Tests for the subcategory_options HTMX endpoint."""

    def test_returns_options_for_category(
        self, authenticated_client: Client, db: None
    ) -> None:
        resp = authenticated_client.get(
            "/items/subcategory-options/?category=ingredient"
        )
        assert resp.status_code == 200
        assert b"hops" in resp.content
        assert b"cleaner" not in resp.content

    def test_empty_for_unknown_category(
        self, authenticated_client: Client, db: None
    ) -> None:
        resp = authenticated_client.get("/items/subcategory-options/?category=unknown")
        assert resp.status_code == 200


class TestRecipeListView:
    """Tests for the recipe_list view."""

    def test_empty_list(self, authenticated_client: Client, db: None) -> None:
        # Delete seeded recipes from migration
        Recipe.objects.all().delete()
        resp = authenticated_client.get("/recipes/")
        assert resp.status_code == 200
        assert b"No recipes yet" in resp.content

    def test_shows_recipes(
        self, authenticated_client: Client, pale_ale_recipe: Recipe
    ) -> None:
        resp = authenticated_client.get("/recipes/")
        assert b"Test Pale Ale" in resp.content


class TestRecipeCreateView:
    """Tests for the recipe_create view."""

    def test_get_form(self, authenticated_client: Client, db: None) -> None:
        resp = authenticated_client.get("/recipes/create/")
        assert resp.status_code == 200

    def test_post_creates_recipe(self, authenticated_client: Client, db: None) -> None:
        data = {
            "name": "Wheat Beer",
            "abv": "5.0",
            "ibu": "20",
            # Formset management data
            "ingredients-TOTAL_FORMS": "3",
            "ingredients-INITIAL_FORMS": "0",
            "ingredients-MIN_NUM_FORMS": "0",
            "ingredients-MAX_NUM_FORMS": "1000",
        }
        resp = authenticated_client.post("/recipes/create/", data)
        assert resp.status_code == 302
        assert Recipe.objects.filter(name="Wheat Beer").exists()


class TestRecipeUpdateView:
    """Tests for the recipe_update view."""

    def test_get_edit_form(
        self, authenticated_client: Client, pale_ale_recipe: Recipe
    ) -> None:
        resp = authenticated_client.get(f"/recipes/{pale_ale_recipe.pk}/edit/")
        assert resp.status_code == 200

    def test_post_updates_recipe(
        self, authenticated_client: Client, pale_ale_recipe: Recipe
    ) -> None:
        data = {
            "name": "Session Pale Ale",
            "abv": "4.5",
            "ibu": "35",
            # Formset management data
            "ingredients-TOTAL_FORMS": "3",
            "ingredients-INITIAL_FORMS": "0",
            "ingredients-MIN_NUM_FORMS": "0",
            "ingredients-MAX_NUM_FORMS": "1000",
        }
        resp = authenticated_client.post(f"/recipes/{pale_ale_recipe.pk}/edit/", data)
        assert resp.status_code == 302
        pale_ale_recipe.refresh_from_db()
        assert pale_ale_recipe.name == "Session Pale Ale"


class TestRecipeDeleteView:
    """Tests for the recipe_delete view."""

    def test_get_confirmation(
        self, authenticated_client: Client, pale_ale_recipe: Recipe
    ) -> None:
        resp = authenticated_client.get(f"/recipes/{pale_ale_recipe.pk}/delete/")
        assert resp.status_code == 200

    def test_post_deletes_recipe(
        self, authenticated_client: Client, pale_ale_recipe: Recipe
    ) -> None:
        resp = authenticated_client.post(f"/recipes/{pale_ale_recipe.pk}/delete/")
        assert resp.status_code == 302
        assert not Recipe.objects.filter(pk=pale_ale_recipe.pk).exists()


class TestRecipeQuickAdd:
    """Tests for the recipe_quick_add HTMX endpoint."""

    def test_get_returns_form(self, authenticated_client: Client, db: None) -> None:
        resp = authenticated_client.get("/recipes/quick-add/")
        assert resp.status_code == 200

    def test_post_creates_recipe(self, authenticated_client: Client, db: None) -> None:
        resp = authenticated_client.post(
            "/recipes/quick-add/", {"recipe_name": "Porter"}
        )
        assert resp.status_code == 200
        assert Recipe.objects.filter(name="Porter").exists()
        assert b"Porter" in resp.content


class TestEarmarkedColumnVisibility:
    """Tests for earmarked column visibility in the item list."""

    def test_earmarked_column_visible_on_all_tab(
        self, authenticated_client: Client, earmarked_item: InventoryItem
    ) -> None:
        resp = authenticated_client.get("/")
        assert b"Earmarked For" in resp.content

    def test_earmarked_column_visible_on_ingredients_tab(
        self, authenticated_client: Client, earmarked_item: InventoryItem
    ) -> None:
        resp = authenticated_client.get("/?category=ingredient")
        assert b"Earmarked For" in resp.content

    def test_earmarked_column_hidden_on_chemicals_tab(
        self, authenticated_client: Client, low_stock_item: InventoryItem
    ) -> None:
        resp = authenticated_client.get("/?category=chemical")
        assert b"Earmarked For" not in resp.content

    def test_earmarked_column_hidden_on_finished_goods_tab(
        self, authenticated_client: Client, keg_item: InventoryItem
    ) -> None:
        resp = authenticated_client.get("/?category=finished_good")
        assert b"Earmarked For" not in resp.content

    def test_earmarked_value_shown_in_row(
        self, authenticated_client: Client, earmarked_item: InventoryItem
    ) -> None:
        resp = authenticated_client.get("/?category=ingredient")
        assert b"Test Pale Ale" in resp.content


class TestItemHistoryView:
    """Tests for the item_history HTMX endpoint."""

    def test_history_returns_partial(
        self, authenticated_client: Client, hop_item: InventoryItem
    ) -> None:
        ItemChangeLog.objects.create(
            item=hop_item,
            action=ActionType.CREATED,
        )
        resp = authenticated_client.get(f"/items/{hop_item.pk}/history/")
        assert resp.status_code == 200
        assert b"Created" in resp.content

    def test_history_empty(
        self, authenticated_client: Client, hop_item: InventoryItem
    ) -> None:
        resp = authenticated_client.get(f"/items/{hop_item.pk}/history/")
        assert resp.status_code == 200
        assert b"No change history" in resp.content


class TestManufacturerSearch:
    """Tests for manufacturer in search functionality."""

    def test_search_by_manufacturer(
        self, authenticated_client: Client, db: None
    ) -> None:
        InventoryItem.objects.create(
            name="2-Row Malt",
            manufacturer="Briess",
            category=Category.INGREDIENT,
            subcategory=Subcategory.MALT,
            quantity_on_hand=Decimal("50.00"),
            unit_of_measure=UnitOfMeasure.LB,
            reorder_point=Decimal("10.00"),
        )
        InventoryItem.objects.create(
            name="2-Row Malt",
            manufacturer="Rahr",
            category=Category.INGREDIENT,
            subcategory=Subcategory.MALT,
            quantity_on_hand=Decimal("25.00"),
            unit_of_measure=UnitOfMeasure.LB,
            reorder_point=Decimal("10.00"),
        )
        resp = authenticated_client.get("/?search=briess")
        assert b"Briess" in resp.content
        assert b"Rahr" not in resp.content

    def test_manufacturer_shown_in_list(
        self, authenticated_client: Client, db: None
    ) -> None:
        InventoryItem.objects.create(
            name="2-Row Malt",
            manufacturer="Viking",
            category=Category.INGREDIENT,
            subcategory=Subcategory.MALT,
            quantity_on_hand=Decimal("50.00"),
            unit_of_measure=UnitOfMeasure.LB,
            reorder_point=Decimal("10.00"),
        )
        resp = authenticated_client.get("/")
        assert b"Viking" in resp.content


class TestChangeLogging:
    """Tests for automatic change logging in views."""

    def test_create_logs_created(self, authenticated_client: Client, db: None) -> None:
        data = {
            "name": "Test Malt",
            "category": Category.INGREDIENT,
            "subcategory": Subcategory.MALT,
            "quantity_on_hand": "50.00",
            "unit_of_measure": UnitOfMeasure.LB,
            "reorder_point": "10.00",
            "description": "",
            "notes": "",
            "earmarked_for": [],
        }
        authenticated_client.post("/items/create/", data)
        item = InventoryItem.objects.get(name="Test Malt")
        logs = ItemChangeLog.objects.filter(item=item)
        assert logs.count() == 1
        assert logs[0].action == ActionType.CREATED

    def test_update_logs_changes(
        self, authenticated_client: Client, hop_item: InventoryItem
    ) -> None:
        data = {
            "name": "Updated Hops",
            "category": Category.INGREDIENT,
            "subcategory": Subcategory.HOPS,
            "quantity_on_hand": "10.00",
            "unit_of_measure": UnitOfMeasure.OZ,
            "reorder_point": "2.00",
            "description": "",
            "notes": "",
            "earmarked_for": [],
        }
        authenticated_client.post(f"/items/{hop_item.pk}/edit/", data)
        logs = ItemChangeLog.objects.filter(item=hop_item, action=ActionType.UPDATED)
        assert logs.count() == 1
        assert logs[0].field_name == "name"
        assert logs[0].old_value == "Cascade Hops"
        assert logs[0].new_value == "Updated Hops"

    def test_adjust_stock_logs_change(
        self, authenticated_client: Client, hop_item: InventoryItem
    ) -> None:
        authenticated_client.post(
            f"/items/{hop_item.pk}/adjust-stock/", {"adjustment": "5.00"}
        )
        logs = ItemChangeLog.objects.filter(
            item=hop_item, action=ActionType.STOCK_ADJUSTED
        )
        assert logs.count() == 1
        assert logs[0].field_name == "quantity_on_hand"
        assert logs[0].old_value == "10.00"
        assert logs[0].new_value == "15.00"
