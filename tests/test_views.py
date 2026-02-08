"""Tests for inventory views."""

from decimal import Decimal

import pytest
from django.test import Client

from inventory.models import Category, InventoryItem, Subcategory, UnitOfMeasure


@pytest.fixture
def client() -> Client:
    return Client()


class TestItemListView:
    """Tests for the item_list view."""

    def test_empty_list(self, client: Client, db: None) -> None:
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"No items found" in resp.content

    def test_shows_items(self, client: Client, hop_item: InventoryItem) -> None:
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Cascade Hops" in resp.content

    def test_filter_by_category(
        self,
        client: Client,
        hop_item: InventoryItem,
        keg_item: InventoryItem,
    ) -> None:
        resp = client.get("/?category=ingredient")
        assert b"Cascade Hops" in resp.content
        assert b"Pale Ale Keg" not in resp.content

    def test_search(
        self,
        client: Client,
        hop_item: InventoryItem,
        keg_item: InventoryItem,
    ) -> None:
        resp = client.get("/?search=cascade")
        assert b"Cascade Hops" in resp.content
        assert b"Pale Ale Keg" not in resp.content

    def test_htmx_returns_partial(
        self, client: Client, hop_item: InventoryItem
    ) -> None:
        resp = client.get("/", HTTP_HX_REQUEST="true")
        assert resp.status_code == 200
        # Partial should NOT include the full base template <html> tag
        assert b"<html" not in resp.content
        assert b"Cascade Hops" in resp.content


class TestItemCreateView:
    """Tests for the item_create view."""

    def test_get_form(self, client: Client, db: None) -> None:
        resp = client.get("/items/create/")
        assert resp.status_code == 200
        assert b"New Item" in resp.content

    def test_post_creates_item(self, client: Client, db: None) -> None:
        data = {
            "name": "2-Row Pale Malt",
            "category": Category.INGREDIENT,
            "subcategory": Subcategory.MALT,
            "quantity_on_hand": "50.00",
            "unit_of_measure": UnitOfMeasure.LB,
            "reorder_point": "10.00",
            "description": "",
            "notes": "",
        }
        resp = client.post("/items/create/", data)
        assert resp.status_code == 302
        assert InventoryItem.objects.filter(name="2-Row Pale Malt").exists()

    def test_post_invalid_data(self, client: Client, db: None) -> None:
        resp = client.post("/items/create/", {"name": ""})
        assert resp.status_code == 200  # Re-renders form with errors


class TestItemDetailView:
    """Tests for the item_detail view."""

    def test_detail_page(self, client: Client, hop_item: InventoryItem) -> None:
        resp = client.get(f"/items/{hop_item.pk}/")
        assert resp.status_code == 200
        assert b"Cascade Hops" in resp.content

    def test_404_for_missing(self, client: Client, db: None) -> None:
        resp = client.get("/items/00000000-0000-0000-0000-000000000000/")
        assert resp.status_code == 404


class TestItemUpdateView:
    """Tests for the item_update view."""

    def test_get_edit_form(self, client: Client, hop_item: InventoryItem) -> None:
        resp = client.get(f"/items/{hop_item.pk}/edit/")
        assert resp.status_code == 200
        assert b"Cascade Hops" in resp.content

    def test_post_updates_item(self, client: Client, hop_item: InventoryItem) -> None:
        data = {
            "name": "Centennial Hops",
            "category": Category.INGREDIENT,
            "subcategory": Subcategory.HOPS,
            "quantity_on_hand": "10.00",
            "unit_of_measure": UnitOfMeasure.OZ,
            "reorder_point": "2.00",
            "description": "",
            "notes": "",
        }
        resp = client.post(f"/items/{hop_item.pk}/edit/", data)
        assert resp.status_code == 302
        hop_item.refresh_from_db()
        assert hop_item.name == "Centennial Hops"


class TestItemDeleteView:
    """Tests for the item_delete view."""

    def test_get_confirmation(self, client: Client, hop_item: InventoryItem) -> None:
        resp = client.get(f"/items/{hop_item.pk}/delete/")
        assert resp.status_code == 200
        assert b"Delete" in resp.content

    def test_post_deletes_item(self, client: Client, hop_item: InventoryItem) -> None:
        resp = client.post(f"/items/{hop_item.pk}/delete/")
        assert resp.status_code == 302
        assert not InventoryItem.objects.filter(pk=hop_item.pk).exists()


class TestAdjustStockView:
    """Tests for the adjust_stock HTMX endpoint."""

    def test_get_returns_form(self, client: Client, hop_item: InventoryItem) -> None:
        resp = client.get(f"/items/{hop_item.pk}/adjust-stock/")
        assert resp.status_code == 200
        assert b"adjustment" in resp.content

    def test_post_adjusts_stock(self, client: Client, hop_item: InventoryItem) -> None:
        resp = client.post(
            f"/items/{hop_item.pk}/adjust-stock/", {"adjustment": "5.00"}
        )
        assert resp.status_code == 200
        hop_item.refresh_from_db()
        assert hop_item.quantity_on_hand == Decimal("15.00")


class TestSubcategoryOptionsView:
    """Tests for the subcategory_options HTMX endpoint."""

    def test_returns_options_for_category(self, client: Client, db: None) -> None:
        resp = client.get("/items/subcategory-options/?category=ingredient")
        assert resp.status_code == 200
        assert b"hops" in resp.content
        assert b"cleaner" not in resp.content

    def test_empty_for_unknown_category(self, client: Client, db: None) -> None:
        resp = client.get("/items/subcategory-options/?category=unknown")
        assert resp.status_code == 200
