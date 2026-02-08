"""Forms for inventory management."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django import forms

from .models import SUBCATEGORY_MAP, InventoryItem


class InventoryItemForm(forms.ModelForm):  # type: ignore[type-arg]
    """Form for creating and updating inventory items."""

    class Meta:
        model = InventoryItem
        fields = [
            "name",
            "category",
            "subcategory",
            "description",
            "quantity_on_hand",
            "unit_of_measure",
            "reorder_point",
            "notes",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.category:
            choices = SUBCATEGORY_MAP.get(self.instance.category, [])
            self.fields["subcategory"].choices = [  # type: ignore[attr-defined]
                ("", "---------"),
                *choices,
            ]


class StockAdjustmentForm(forms.Form):
    """Form for quick stock adjustments."""

    adjustment = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Positive to add, negative to subtract.",
    )

    def apply_to(self, item: InventoryItem) -> InventoryItem:
        """Apply the stock adjustment to the given item."""
        adjustment: Decimal = self.cleaned_data["adjustment"]
        item.quantity_on_hand += adjustment
        if item.quantity_on_hand < Decimal("0.00"):
            item.quantity_on_hand = Decimal("0.00")
        item.save(update_fields=["quantity_on_hand", "updated_at"])
        return item
