"""Inventory app configuration."""

from django.apps import AppConfig


class InventoryConfig(AppConfig):
    """Configuration for the inventory application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "inventory"
