"""Tests for stock alert notification system."""

from decimal import Decimal
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.test import Client, RequestFactory

from inventory.models import Category, InventoryItem, Subcategory, UnitOfMeasure
from inventory.notifications import (
    SESSION_KEY,
    StockAlert,
    clear_pending_alerts,
    get_pending_alerts,
    queue_stock_alert,
    send_stock_alert_email,
)


@pytest.fixture
def request_with_session(authenticated_client: Client) -> Client:
    """Return authenticated client with initialized session."""
    # Make a request to initialize the session
    authenticated_client.get("/")
    return authenticated_client


class TestQueueStockAlert:
    """Tests for queue_stock_alert function."""

    def test_queues_alert_on_transition_to_low(
        self, request_with_session: Client, hop_item: InventoryItem
    ) -> None:
        factory = RequestFactory()
        request = factory.get("/")
        request.session = request_with_session.session

        queue_stock_alert(request, hop_item, "ok", "low")

        alerts = request.session.get(SESSION_KEY, [])
        assert len(alerts) == 1
        assert alerts[0]["item_name"] == "Cascade Hops"
        assert alerts[0]["new_status"] == "low"

    def test_queues_alert_on_transition_to_reorder(
        self, request_with_session: Client, hop_item: InventoryItem
    ) -> None:
        factory = RequestFactory()
        request = factory.get("/")
        request.session = request_with_session.session

        queue_stock_alert(request, hop_item, "ok", "reorder")

        alerts = request.session.get(SESSION_KEY, [])
        assert len(alerts) == 1
        assert alerts[0]["new_status"] == "reorder"

    def test_does_not_queue_for_ok_status(
        self, request_with_session: Client, hop_item: InventoryItem
    ) -> None:
        factory = RequestFactory()
        request = factory.get("/")
        request.session = request_with_session.session

        queue_stock_alert(request, hop_item, "low", "ok")

        alerts = request.session.get(SESSION_KEY, [])
        assert len(alerts) == 0

    def test_does_not_queue_when_already_critical(
        self, request_with_session: Client, hop_item: InventoryItem
    ) -> None:
        factory = RequestFactory()
        request = factory.get("/")
        request.session = request_with_session.session

        # low -> reorder should not notify (already in critical state)
        queue_stock_alert(request, hop_item, "low", "reorder")

        alerts = request.session.get(SESSION_KEY, [])
        assert len(alerts) == 0

    def test_queues_multiple_alerts(
        self, request_with_session: Client, hop_item: InventoryItem, db: None
    ) -> None:
        factory = RequestFactory()
        request = factory.get("/")
        request.session = request_with_session.session

        item2 = InventoryItem.objects.create(
            name="Another Item",
            category=Category.INGREDIENT,
            subcategory=Subcategory.MALT,
            quantity_on_hand=Decimal("5.00"),
            unit_of_measure=UnitOfMeasure.LB,
            reorder_point=Decimal("10.00"),
        )

        queue_stock_alert(request, hop_item, "ok", "low")
        queue_stock_alert(request, item2, "ok", "reorder")

        alerts = request.session.get(SESSION_KEY, [])
        assert len(alerts) == 2


class TestClearPendingAlerts:
    """Tests for clear_pending_alerts function."""

    def test_clears_alerts(self, request_with_session: Client) -> None:
        factory = RequestFactory()
        request = factory.get("/")
        request.session = request_with_session.session
        request.session[SESSION_KEY] = [{"item_name": "Test"}]

        clear_pending_alerts(request)

        assert SESSION_KEY not in request.session

    def test_handles_no_alerts(self, request_with_session: Client) -> None:
        factory = RequestFactory()
        request = factory.get("/")
        request.session = request_with_session.session

        # Should not raise
        clear_pending_alerts(request)


class TestGetPendingAlerts:
    """Tests for get_pending_alerts function."""

    def test_returns_alerts(self, request_with_session: Client) -> None:
        factory = RequestFactory()
        request = factory.get("/")
        request.session = request_with_session.session
        request.session[SESSION_KEY] = [{"item_name": "Test"}]

        alerts = get_pending_alerts(request)

        assert len(alerts) == 1
        assert alerts[0]["item_name"] == "Test"

    def test_returns_empty_list_when_none(self, request_with_session: Client) -> None:
        factory = RequestFactory()
        request = factory.get("/")
        request.session = request_with_session.session

        alerts = get_pending_alerts(request)

        assert alerts == []


class TestSendStockAlertEmail:
    """Tests for send_stock_alert_email function."""

    def test_sends_email_to_user_with_email(self, user: User) -> None:
        user.email = "test@example.com"
        user.save()

        alerts: list[StockAlert] = [
            {
                "item_id": "123",
                "item_name": "Test Hops",
                "old_status": "ok",
                "new_status": "low",
                "quantity": "5.00",
                "reorder_point": "10.00",
                "unit": "oz",
                "timestamp": "2026-02-15T12:00:00",
            }
        ]

        with patch("inventory.notifications.send_mail") as mock_send:
            result = send_stock_alert_email(user, alerts)

        assert result is True
        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args.kwargs
        assert "test@example.com" in call_kwargs["recipient_list"]
        assert "1 item(s)" in call_kwargs["subject"]

    def test_returns_false_for_user_without_email(self, user: User) -> None:
        user.email = ""
        user.save()

        alerts: list[StockAlert] = [
            {
                "item_id": "123",
                "item_name": "Test",
                "old_status": "ok",
                "new_status": "low",
                "quantity": "5.00",
                "reorder_point": "10.00",
                "unit": "oz",
                "timestamp": "2026-02-15T12:00:00",
            }
        ]

        result = send_stock_alert_email(user, alerts)

        assert result is False

    def test_returns_false_for_empty_alerts(self, user: User) -> None:
        user.email = "test@example.com"
        user.save()

        result = send_stock_alert_email(user, [])

        assert result is False

    def test_separates_reorder_and_low_alerts(self, user: User) -> None:
        user.email = "test@example.com"
        user.save()

        alerts: list[StockAlert] = [
            {
                "item_id": "1",
                "item_name": "Critical Item",
                "old_status": "ok",
                "new_status": "reorder",
                "quantity": "1.00",
                "reorder_point": "5.00",
                "unit": "lb",
                "timestamp": "2026-02-15T12:00:00",
            },
            {
                "item_id": "2",
                "item_name": "Low Item",
                "old_status": "ok",
                "new_status": "low",
                "quantity": "6.00",
                "reorder_point": "5.00",
                "unit": "oz",
                "timestamp": "2026-02-15T12:00:00",
            },
        ]

        with patch("inventory.notifications.send_mail") as mock_send:
            result = send_stock_alert_email(user, alerts)

        assert result is True
        call_kwargs = mock_send.call_args.kwargs
        assert "2 item(s)" in call_kwargs["subject"]


class TestLogoutWithNotifications:
    """Tests for logout view with notification sending."""

    def test_logout_sends_pending_alerts(self, user: User, db: None) -> None:
        user.email = "test@example.com"
        user.save()

        client = Client()
        client.login(username="testuser", password="testpass123")

        # Add an alert to the session
        session = client.session
        session[SESSION_KEY] = [
            {
                "item_id": "123",
                "item_name": "Test Item",
                "old_status": "ok",
                "new_status": "reorder",
                "quantity": "1.00",
                "reorder_point": "5.00",
                "unit": "each",
                "timestamp": "2026-02-15T12:00:00",
            }
        ]
        session.save()

        with patch("inventory.views.send_stock_alert_email") as mock_send:
            mock_send.return_value = True
            response = client.get("/logout/")

        mock_send.assert_called_once()
        assert response.status_code == 302

    def test_logout_works_without_alerts(self, authenticated_client: Client) -> None:
        response = authenticated_client.get("/logout/")
        assert response.status_code == 302

    def test_logout_works_when_user_has_no_email(self, user: User, db: None) -> None:
        user.email = ""
        user.save()

        client = Client()
        client.login(username="testuser", password="testpass123")

        session = client.session
        session[SESSION_KEY] = [
            {
                "item_id": "123",
                "item_name": "Test Item",
                "old_status": "ok",
                "new_status": "low",
                "quantity": "1.00",
                "reorder_point": "5.00",
                "unit": "lb",
                "timestamp": "2026-02-15T12:00:00",
            }
        ]
        session.save()

        response = client.get("/logout/")
        assert response.status_code == 302


class TestStockAlertIntegration:
    """Integration tests for stock alert flow."""

    def test_adjust_stock_queues_alert_on_status_change(
        self, authenticated_client: Client, db: None
    ) -> None:
        # Create item with stock above reorder
        item = InventoryItem.objects.create(
            name="Alert Test Hops",
            category=Category.INGREDIENT,
            subcategory=Subcategory.HOPS,
            quantity_on_hand=Decimal("10.00"),
            unit_of_measure=UnitOfMeasure.OZ,
            reorder_point=Decimal("5.00"),
        )
        assert item.stock_status == "ok"

        # Adjust stock to trigger low status (within 10% of reorder point)
        authenticated_client.post(
            f"/items/{item.pk}/adjust-stock/", {"adjustment": "-4.50"}
        )

        item.refresh_from_db()
        assert item.stock_status == "low"

        # Check session has alert
        session = authenticated_client.session
        alerts = session.get(SESSION_KEY, [])
        assert len(alerts) == 1
        assert alerts[0]["item_name"] == "Alert Test Hops"
        assert alerts[0]["new_status"] == "low"

    def test_adjust_stock_to_reorder_queues_alert(
        self, authenticated_client: Client, db: None
    ) -> None:
        item = InventoryItem.objects.create(
            name="Critical Test Item",
            category=Category.CHEMICAL,
            subcategory=Subcategory.CLEANER,
            quantity_on_hand=Decimal("10.00"),
            unit_of_measure=UnitOfMeasure.LB,
            reorder_point=Decimal("5.00"),
        )

        # Adjust to reorder status
        authenticated_client.post(
            f"/items/{item.pk}/adjust-stock/", {"adjustment": "-6.00"}
        )

        item.refresh_from_db()
        assert item.stock_status == "reorder"

        session = authenticated_client.session
        alerts = session.get(SESSION_KEY, [])
        assert len(alerts) == 1
        assert alerts[0]["new_status"] == "reorder"

    def test_no_alert_when_status_unchanged(
        self, authenticated_client: Client, hop_item: InventoryItem
    ) -> None:
        # hop_item has qty=10, reorder=2, so status is 'ok'
        # Small adjustment should keep status as 'ok'
        authenticated_client.post(
            f"/items/{hop_item.pk}/adjust-stock/", {"adjustment": "-1.00"}
        )

        hop_item.refresh_from_db()
        assert hop_item.stock_status == "ok"

        session = authenticated_client.session
        alerts = session.get(SESSION_KEY, [])
        assert len(alerts) == 0
